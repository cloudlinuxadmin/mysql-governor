# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
"""
This module contains class for managing governor on cPanel server
"""
import os
import re
import shutil
import sys
import urllib2
import hashlib

from utilities import exec_command_out, grep, add_line, \
    service, remove_lines, write_file, replace_lines, touch, \
    is_package_installed, remove_packages, exec_command, parse_rpm_name, service_symlink, bcolors
from .base import InstallManager


class cPanelManager(InstallManager):
    """
    Installation manager for cPanel
    """

    def update_user_map_file(self):
        """
        Update user mapping file for cPanel
        """
        try:
            self._script_subprocess("dbgovernor_map")
        except RuntimeError as e:
            self.warning(str(e))

    def warning(self, orig_msg):
        """
        Warn user in case of errors during dbgovernor_map process and exit with exitcode 1.
        If CpuserNotInMap Exception occurred, advice user to run rebuild_dbmap script
        Otherwise, just show original exception
        :param orig_msg: original exception text
        """
        if 'CpuserNotInMap' in orig_msg:
            username = self.retrieve_username(orig_msg)
            print bcolors.fail('cPanel user `{u}` does not exist in the database map.'.format(u=username))
            print bcolors.info('Try to perform the following command: /scripts/rebuild_dbmap {u}\n'
                               'and then run /usr/share/lve/dbgovernor/mysqlgovernor.py --dbupdate again.'.format(u=username))
            print bcolors.warning('If this does not help, please, '
                                  'contact cPanel support with the original error:\n{m}'.format(u=username,
                                                                                                m=orig_msg.split('\n')[1]))
        else:
            print bcolors.fail(orig_msg)
        sys.exit(1)

    @staticmethod
    def retrieve_username(msg):
        """
        Try to get corrupted user name from the exception text (e.g. CpuserNotInMap Exception)
        :param msg: original exception text
        :return: username if retrieved, None otherwise
        """
        try:
            return re.findall('cPanel user \xE2\x80\x9C(.+)\xE2\x80\x9D does not exist in the database map.', msg)[0]
        except IndexError:
            return None

    def install_mysql_beta_testing_hooks(self):
        """
        Specific hooks
        """
        self.set_fs_suid_dumpable()
        self._script("cpanel-install-hooks")

    def _delete(self, installed_packages):
        """
        Remove installed packages
        """
        # through mysql --version cmd
        current_version = self._check_mysql_version()

        if os.path.exists("/etc/chkserv.d/db_governor"):
            os.remove("/etc/chkserv.d/db_governor")
        self._script("chek_mysql_rpms_local", "-d")
        self._script("cpanel-delete-hooks")

        if os.path.exists("/etc/mysqlupdisable"):
            os.remove("/etc/mysqlupdisable")

        if os.path.exists("/var/cpanel/rpm.versions.d/cloudlinux.versions"):
            os.remove("/var/cpanel/rpm.versions.d/cloudlinux.versions")

        if os.path.exists("/etc/cpupdate.conf.governor"):
            if os.path.exists("/etc/cpupdate.conf"):
                os.remove("/etc/cpupdate.conf")
            os.rename("/etc/cpupdate.conf.governor", "/etc/cpupdate.conf")

        self._mysqlservice("stop")
        # remove governor package
        exec_command_out("rpm -e governor-mysql")
        # delete installed packages
        remove_packages(installed_packages)

        self.restore_mysql_packages(current_version)
        exec_command_out("/scripts/upcp --force")

    def restore_mysql_packages(self, current_version):
        """
        Install legacy packages after --delete procedure
        """
        print 'Restoring known packages for {}'.format(current_version['full'])
        targets = {
            'mysql55': 'MySQL55',
            'mysql56': 'MySQL56',
            'mariadb100': 'MariaDB100',
            'mariadb101': 'MariaDB101',
            'mariadb102': 'MariaDB102',
            'mariadb103': 'MariaDB103',
        }
        old = 'MySQL50,MySQL51,'  # old unsupported targets
        not_managed = ('mysql57', 'mysql80')  # latest mysql not managed by cPanel
        # clear rpm management for all known targets
        for t in targets.values():
            exec_command('/usr/local/cpanel/scripts/update_local_rpm_versions --del target_settings.%(target)s' % {'target': t})
        # disable mysql targets for upcp not to fix them!
        for k in filter(lambda x: 'mariadb' not in x and x != current_version['full'], targets.keys()):
            exec_command('/usr/local/cpanel/scripts/update_local_rpm_versions --edit target_settings.%(target)s uninstalled' % {'target': targets[k]})

        # update mysql version in cPanel's configuration file
        exec_command(self._rel("scripts/set_cpanel_mysql_version.pm %s" % current_version['short']))

        if current_version['mysql_type'] == 'mariadb':
            # add repo, yum install mariadb pkgs
            self.install_mariadb(current_version['full'])
        elif current_version['full'] in not_managed:
            # add repo, yum install mysql57 or mysql80
            self.install_mysql_community(current_version['full'])
            # create mysql alias for mysqld service
            self.mysql_service_symlink()
        else:
            # enable current mysql target to rpm management
            t = targets.get(current_version['full'])
            if not t:
                raise RuntimeError('unknown target for RPM management: {}'.format(current_version['full']))
            exec_command('/usr/local/cpanel/scripts/update_local_rpm_versions --edit target_settings.%(target)s installed' % {'target': t})
            # fix legacy RPMs (works for mysql55 and mysql56 only)
            if os.path.exists("/scripts/check_cpanel_rpms"):
                exec_command_out(
                    "/scripts/check_cpanel_rpms --fix --targets={}".format(
                        old + ','.join(targets.values())))
            # clear RPM management targets for cPanel higher than 72 version,
            # because setting it to `installed` causes MySQL/MariaDB Upgrade interface errors
            if self.get_panel_version() > 72:
                exec_command('/usr/local/cpanel/scripts/update_local_rpm_versions --del target_settings.%(target)s' % {'target': t})

    def install_mariadb(self, version):
        """
        Install official MariaDB
        """
        pkgs = ('MariaDB-server', 'MariaDB-client', 'MariaDB-shared',
                'MariaDB-devel', 'MariaDB-compat',)
        # prepare repo data
        print 'Preparing official MariaDB repository...'
        repo_data = """[mariadb]
name = MariaDB
baseurl = http://yum.mariadb.org/{maria_ver}/centos{cl_ver}-{arch}
gpgkey=https://yum.mariadb.org/RPM-GPG-KEY-MariaDB
gpgcheck=1
"""
        num = version.split('mariadb')[-1]
        mariadb_version = '{base}.{suffix}'.format(base=num[:-1],
                                                   suffix=num[-1])
        arch = 'amd64' if os.uname()[-1] == 'x86_64' else 'x86'
        with open('/etc/yum.repos.d/MariaDB.repo', 'wb') as repo_file:
            repo_file.write(
                repo_data.format(maria_ver=mariadb_version,
                                 cl_ver=self.cl_version, arch=arch))

        # install MariaDB packages
        print 'Installing packages'
        exec_command(
            "yum install -y --disableexcludes=all --disablerepo=cl-mysql* --disablerepo=mysqclient* {pkgs}".format(
                pkgs=' '.join(pkgs)))

    def install_mysql_community(self, version):
        """
        Install official MySQL 5.7 or MySQL 8.0, not managed by cPanel
        """
        pkgs = ('mysql-community-server', 'mysql-community-client',
               'mysql-community-common', 'mysql-community-libs')
        # prepare mysql repo
        if not exec_command('rpm -qa | grep mysql80-community', silent=True):
            self.download_and_install_mysql_repo()

        # select MySQL version
        print 'Selected version %s' % version
        exec_command('yum-config-manager --disable mysql*-community')
        exec_command('yum-config-manager --enable {version}-community'.format(version=version))

        # install mysql-community packages
        print 'Installing packages'
        exec_command(
            "yum install -y --disableexcludes=all --disablerepo=cl-mysql* --disablerepo=mysqclient* {pkgs}".format(
                pkgs=' '.join(pkgs)))

    def download_and_install_mysql_repo(self):
        """
        Download mysql80-community-release repository and install it locally
        """
        # download repo file
        url = 'https://dev.mysql.com/get/mysql80-community-release-el{v}-1.noarch.rpm'.format(v=self.cl_version)
        repo_file = os.path.join(self.SOURCE, 'mysql-community-release.rpm')
        repo_md5 = {
            6: 'f2befc44a4b8416864987b1686c4a72b',
            7: '739dc44566d739c5d7b893de96ee6848'
        }
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]

        print 'Downloading %s' % url
        rpm = opener.open(url).read()
        with open(repo_file, 'wb') as f:
            f.write(rpm)

        if hashlib.md5(open(repo_file, 'rb').read()).hexdigest() != repo_md5[self.cl_version]:
            print 'Failed to download MySQL repository file. File is corrupted!'
            sys.exit(1)

        # install repo
        exec_command_out('yum localinstall -y --disableexcludes=all {}'.format(repo_file))

    @staticmethod
    def mysql_service_symlink():
        """
        Create mysql alias for mysqld service
        """
        service_symlink('mysqld', 'mysql')
        # delete version cache (for web-interface correct version detection)
        try:
            os.unlink('/var/cpanel/mysql_server_version_cache')
            os.unlink('/var/lib/mysql/mysql_upgrade_info')
        except Exception:
            pass

    def check_need_for_mysql_upgrade(self):
        """
        Check for upgrading mysql tables on cPanel is specific
        because cPanel manages its own upgrade scripts for MySQL.
        That is why the True condition for mysql_upgrade is
            if MySQL became MariaDB
            if MariaDB version has changed
        :return: should upgrade or not (True or False)
        """
        current_version = self._check_mysql_version()
        if not self.prev_version or not current_version:
            print 'Problem with version retrieving'
            return False
        return current_version['mysql_type'] == 'mariadb' and \
               (self.prev_version['mysql_type'] == 'mysql' or
                current_version['short'] != self.prev_version['short'])

    def _after_install_new_packages(self):
        """
        cPanel triggers after install new packages to system
        """
        # cpanel script for restart mysql service
        exec_command_out("/scripts/restartsrv_mysql")

        print "db_governor checking: "
        if is_package_installed("governor-mysql"):
            exec_command_out("chkconfig --level 35 db_governor on")
            service("restart", "db_governor")
            print "OK"
        else:
            print "FAILED"

        # print "The installation of MySQL for db_governor completed"

        if os.path.exists("/usr/local/cpanel/cpanel"):
            if os.path.exists(
                    "/usr/local/cpanel/scripts/update_local_rpm_versions"):
                shutil.copy2(self._rel("utils/cloudlinux.versions"), "/var/cpanel/rpm.versions.d/cloudlinux.versions")
            else:
                if not os.path.exists("/etc/cpupdate.conf.governor"):
                    self._get_mysqlup()
                touch("/etc/mysqlupdisable")

        self._script("cpanel-install-hooks")

        if os.path.exists("/usr/local/cpanel/cpanel") and \
                os.path.exists(
                    "/usr/local/cpanel/scripts/update_local_rpm_versions"):
            if os.path.exists("/etc/mysqlupdisable"):
                os.unlink("/etc/mysqlupdisable")
            remove_lines("/etc/cpupdate.conf", "MYSQLUP=never")
        if os.path.exists("/etc/chkserv.d") and os.path.exists(
                self._rel("utils/db_governor")):
            shutil.copy2(self._rel("utils/db_governor"),
                         "/etc/chkserv.d/db_governor")
        # call parent after_install
        InstallManager._after_install_new_packages(self)

    def _after_install_rollback(self):
        """
        Rollback after install triggers
        """
        # if os.path.exists("/etc/mysqlupdisable"):
        #     os.remove("/etc/mysqlupdisable")

        # if os.path.exists("/var/cpanel/rpm.versions.d/cloudlinux.versions"):
        #     os.remove("/var/cpanel/rpm.versions.d/cloudlinux.versions")

        # if os.path.exists("/etc/cpupdate.conf.governor"):
        #     if os.path.exists("/etc/cpupdate.conf"):
        #         os.remove("/etc/cpupdate.conf")
        #     os.rename("/etc/cpupdate.conf.governor", "/etc/cpupdate.conf")

        # exec_command_out(SOURCE+"cpanel/cpanel-delete-hooks")

        # exec_command_out("/scripts/upcp --force")
        # if os.path.exists("/scripts/check_cpanel_rpms"):
        #     exec_command_out("/scripts/check_cpanel_rpms --fix --targets=MySQL50,MySQL51,MySQL55,MySQL56,MariaDB")

    #############################
    #############################
    #############################
    # if os.path.exists("/var/cpanel/rpm.versions.d/cloudlinux.versions"):
    #     os.unlink("/var/cpanel/rpm.versions.d/cloudlinux.versions")

    # exec_command_out(SOURCE+"cpanel/cpanel-delete-hooks")

    # remove_lines("/etc/cpupdate.conf", "MYSQLUP=never")
    # if os.path.exists("/etc/cpupdate.conf.governor"):
    #     os.unlink("/etc/cpupdate.conf.governor")

    # if os.path.exists("/etc/mysqlupdisable"):
    #     os.unlink("/etc/mysqlupdisable")

    def _before_delete(self):
        """
        Disable mysql service monitoring
        """
        self.enable_mysql_monitor(False)

    def _after_delete(self):
        """
        Enable mysql service monitoring
        """
        # call parent first
        InstallManager._after_delete(self)
        self.enable_mysql_monitor()

    def _before_install(self):
        """
        Disable mysql service monitoring
        """
        self.enable_mysql_monitor(False)

    def _after_install(self):
        """
        Enable mysql service monitoring
        """
        # call parent first
        InstallManager._after_install(self)
        self.enable_mysql_monitor()

    @staticmethod
    def _get_mysqlup():
        """
        ? Set value for panel update MYSQLUP option
        """
        if os.path.exists("/etc/cpupdate.conf"):
            shutil.copy2("/etc/cpupdate.conf", "/etc/cpupdate.conf.governor")
            is_mysqlup = grep("/etc/cpupdate.conf", "MYSQLUP")
            if is_mysqlup:
                if not grep(is_mysqlup, "never$", True):
                    replace_lines("/etc/cpupdate.conf", "".join(is_mysqlup),
                                  "MYSQLUP=never")
            else:
                add_line("/etc/cpupdate.conf", "\nMYSQLUP=never\n")
        else:
            write_file("/etc/cpupdate.conf.governor", "")
            write_file("/etc/cpupdate.conf", "MYSQLUP=never\n")

    def _detect_version_if_auto(self):
        """
        Detect vesrion of MySQL if mysql.type is auto
        """
        if os.path.exists(self._rel("scripts/detect-cpanel-mysql-version.pm")):
            mysqlname_array = exec_command(
                self._rel("scripts/detect-cpanel-mysql-version.pm"))
            mysqlname = ""
            if len(mysqlname_array) > 0:
                mysqlname = mysqlname_array[0]
            if "mysql" in mysqlname or "mariadb" in mysqlname:
                return mysqlname.strip()
        return ""

    def _custom_download_of_rpm(self, package_name):
        """
        How we should to download installed MySQL package
        """
        if package_name == "+":
            return "yes"

        result = parse_rpm_name(package_name)
        if len(result) == 4:
            return exec_command(self._rel(
                "scripts/cpanel-mysql-url-detect.pm %s %s-%s" % (
                    result[0], result[1], result[2])), True)
        return ""

    def make_additional_panel_related_check(self):
        """
        Specific cPanel check
        :return:
        """
        if os.path.exists("/usr/local/cpanel/cpanel"):
            if os.path.exists(
                    "/usr/local/cpanel/scripts/update_local_rpm_versions") and \
                    os.path.exists(
                        "/var/cpanel/rpm.versions.d/cloudlinux.versions") and \
                    os.path.exists(
                        self._rel("utils/cloudlinux.versions")):
                shutil.copy2(self._rel("utils/cloudlinux.versions"),
                             "/var/cpanel/rpm.versions.d/cloudlinux.versions")
        return

    @staticmethod
    def enable_mysql_monitor(enable=True):
        """
        Enable or disable mysql monitoring
        :param enable: if True - enable monitor
                       if False - disable monitor
        """
        exec_command_out(
            "whmapi1 configureservice service=mysql enabled=1 monitored={}".format(int(enable)))

    @staticmethod
    def get_panel_version():
        """
        Retrieve cPanel current version from /usr/local/cpanel/version file
        :return: major version value
        """
        with open('/usr/local/cpanel/version', 'rb') as content:
            full_version = content.read().strip()
        return int(full_version.split('.')[1])
