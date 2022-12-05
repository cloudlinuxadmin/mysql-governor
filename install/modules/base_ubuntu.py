# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
"""
This module contains base class for managing governor on Ubuntu
"""
import os
import sys
import time
import pwd
import grp
import re
import shutil


sys.path.append("../")

from utilities import exec_command, service, touch, \
    download_apt_packages, is_package_installed, \
    confirm_packages_installation, create_mysqld_link, \
    correct_remove_notowned_mysql_service_names_cl7, \
    correct_remove_notowned_mysql_service_names_not_symlynks_cl7, get_mysql_log_file, \
    makedir_recursive, bcolors, show_new_packages_info, wizard_install_confirm, \
    is_ubuntu, install_deb_from_url, install_deb_packages, check_mysql_compatibilty, \
    check_file

from .base import InstallManager

CLOUDLINUX_RELEASE = 'https://repo.cloudlinux.com/cloudlinux-ubuntu/cloudlinux/stable/cloudlinux-release-latest-20_04.deb'
DEB_TEMP_PATH = "/usr/share/lve/dbgovernor/tmp/governor-tmp"

class UbuntuInstallManager(InstallManager):
    """
    Base class with standard methods for Ubuntu inherited from InstallManager
    """

    IS_UBUNTU = is_ubuntu()

    def __init__(self, cp_name):
        super().__init__(cp_name)
        self.cl_version = 8
        self.new_version_of_db = self._get_new_version()
        self.cp_name = cp_name
        self.panel_manager = InstallManager.factory(cp_name)

    def install_mysql_beta_testing_hooks(self):
        """
        cPanel specific action
        """
        self.panel_manager.install_mysql_beta_testing_hooks()

    def update_mysql_hooks(self):
        """
        cPanel specific action
        """
        self.panel_manager.update_mysql_hooks()

    def fix_mysqld_service(self):
        """
        DA specific action
        """
        self.panel_manager.fix_mysqld_service()

    def check_and_install_needed_packages(self):
        """Install packages needed if not installed
        This function is used to install some dependencies before governor install new download packages
        Some packages needs to be installed before
        """
        if 'mysql' in self.new_version_of_db or self.new_version_of_db == 'auto':
            needed_packages = ['mysql-common', 'mariadb-common']
        elif 'mariadb' in self.new_version_of_db:
            needed_packages = ['cl-mariadb103-common']

        must_be_installed = []
        for package in needed_packages:
            if not is_package_installed(package):
                must_be_installed.append(package)
        if must_be_installed:
            exec_command(f'apt-get install -y {" ".join(str(package) for package in must_be_installed)}')

    def install(self, beta, no_confirm, wizard_mode):
        """
        Install stable or beta packages
        Args:
            beta (bool) : install beta or production
            path (str)  : path to packages for install
            wizard_mode : wizard mode
            cp_name (string) : Panel name
        """
        if not self.cl_version:
            print("Unknown system type. Installation aborted")
            sys.exit(1)

        self._before_install()

        if self.cp_name == 'cPanel':
            self.panel_manager.prepare_statement_for_ubuntu()

        # remember installed mysql version
        self.prev_version = self._check_mysql_version()
        if not hasattr(self.panel_manager, 'prev_version'):
            setattr(self.panel_manager, 'prev_version', self.prev_version)
        self.new_packages = self.get_new_packages()

        # Check new mysql version. Downgrade not supported
        # If new version is less than currently installed one exit
        for package in self.new_packages:
            if 'mysql-server-8.0' in package:
                check_mysql_compatibilty(self.prev_version, 'mysql-server-8.0')
                break


        # first download packages for current and new mysql versions
        self._load_packages(beta)

        # save current installed mysql version
        self._save_previous_version()

        if self.ALL_PACKAGES_NEW_NOT_DOWNLOADED:
            self.print_warning_about_not_complete_of_newpkg_saving()
            return False

        if self.ALL_PACKAGES_OLD_NOT_DOWNLOADED:
            self.print_warning_about_not_complete_of_pkg_saving()

        new_version = show_new_packages_info("new")

        if wizard_mode:
            # wizard mode has its own confirmation logic
            if not wizard_install_confirm(new_version, self.prev_version):
                sys.exit(3)
        elif not confirm_packages_installation(new_version,
                                               self.prev_version,
                                               no_confirm):
            self.DISABLED = True
            return False

        self.my_cnf_manager('backup')

        create_mysqld_link("mysqld", "mysql")
        create_mysqld_link("mysql", "mysqld")

        # first remove installed mysql packages
        self.remove_current_packages()

        correct_remove_notowned_mysql_service_names_cl7()
        correct_remove_notowned_mysql_service_names_not_symlynks_cl7()

        # restore my.cnf, because removing of packages
        # renames /etc/my.cnf to /etc/my.cnf.rpmsave
        # if os.path.exists("/etc/my.cnf.rpmsave"):
        #     shutil.copy2("/etc/my.cnf.rpmsave", "/etc/my.cnf")
        self.my_cnf_manager('restore_rpmsave')

        self.set_fs_suid_dumpable()
        self._check_leave_pid()

        self._before_install_new_packages()

        # don`t know for what this
        self._kill_mysql()

        self.check_and_install_needed_packages()

        try:
            # new db version which will be installing
            if not install_deb_packages("new"):
                # if not install new packages - don`t do next actions
                return False
        except RuntimeError:
            return False

        create_mysqld_link("mysqld", "mysql")
        create_mysqld_link("mysql", "mysqld")

        self.my_cnf_manager('touch')
        # check if log MySQL's log file exists and correct perms
        # in other case MySQL will not starts
        log_file = get_mysql_log_file()
        makedir_recursive(log_file)
        touch(log_file)
        log_owner_name = pwd.getpwuid(os.stat(log_file).st_uid)[0]
        log_owner_grp = grp.getgrgid(os.stat(log_file).st_gid)[0]
        if log_owner_name != "mysql" or log_owner_grp != "mysql":
            target_uid = pwd.getpwnam("mysql").pw_uid
            target_gid = grp.getgrnam("mysql").gr_gid
            os.chown(log_file, target_uid, target_gid)

        self.my_cnf_inspect()

        version = self._get_new_version()

        if version.startswith("mysql"):
            self._enable_mysql()
        elif version.startswith("percona"):
            self._enable_percona()

        self._mysqlservice("restart")

        print("Giving mysqld a few seconds to start up...")
        time.sleep(5)

        if is_package_installed("governor-mysql"):
            service("restart", "db_governor")
            print(bcolors.ok("DB-Governor installed/updated..."))

        self.panel_manager._after_install_new_packages()

        self._ld_fix()

        self._after_install()

        return True

    def _load_current_packages(self, download=True, folder="old"):
        """
        here we download current installed packages
        @param `download` bool: download rpm files or
                                only return list of installed packages
        """
        print(bcolors.info("Start download current installed packages"))
        PATTERNS = ["cl-mysql", "cl-mariadb", "cl-percona", "mysql", "mariadb",
                    "compat-mysql5", "Percona", "libmaria"]
        mysqld_path = exec_command("which mysqld", True, silent=True)
        pkg_name = False
        if mysqld_path:
            # print "No mysql presents on system"
            # return None

            # server package name
            check_if_mysql_installed = exec_command("""dpkg -S %s """ %
                                                    mysqld_path, True,
                                                    silent=True,
                                                    return_code=True)
            if check_if_mysql_installed == "no":
                print("No mysql packages installed, " \
                      "but mysqld file presents on system")
                pkg_name = None
            else:
                pkg_name = exec_command("""dpkg -S %s """ % mysqld_path, True, silent=True)
                pkg_name = pkg_name.split(":")[0]

        # grep cl-MySQL packages in installed list
        packages = exec_command("""apt list --installed |grep -iE "^(%s)" """ %
                                "|".join(PATTERNS), silent=True)

        # apt list --installed output example:
        # mysql-server-8.0/unknown,now 1:8.0.27-0ubuntu0.20.04.1+cloudlinux1.1 amd64 [installed,auto-removable
        # In this code block we split and clear output string. Package name will be mysql-server-8.0 after cleaning

        for index, _ in enumerate(packages):
            packages[index] = packages[index].split('/')[0]

        """
        match pattern to exclude:
          - MySQL-python package
          - mysqld_exporter package
          - mysql-community release package
          - mysql-common
        from the list of packages to download
        """
        pattern = r'MySQL-python|mysql(d_exporter|\d+-community-release)|mysql-common'
        packages = [x for x in packages if not re.match(pattern, x)]

        if not len(packages):
            print("No installed DB packages found")
            return False

        if pkg_name:
            found = False
            for pkg in packages:
                if pkg.startswith(pkg_name):
                    found = True
                    break

            if not found:
                packages.append(pkg_name)

        if download:
            """
            arch = ".x86_64" if os.uname()[-1] == "x86_64" else ""
            download_pkgs = ["%s%s" % (x.split(" ")[0], arch)
            for x in packages]
            """
            IS_CL_MYSQL = False
            for package_item in packages:
                if "server" in package_item and package_item[:3] == "cl-":
                    IS_CL_MYSQL = True

            if IS_CL_MYSQL is True:
                if not download_apt_packages(packages, folder, False):
                    self.ALL_PACKAGES_OLD_NOT_DOWNLOADED = True
            else:
                print(bcolors.info("Trying to load custom packages from apt"))
                if not download_apt_packages(packages, folder, False):
                    self.ALL_PACKAGES_OLD_NOT_DOWNLOADED = True
        return packages

    def get_new_packages(self, sql_version=None):
        """detect packages for new installation"""
        print(bcolors.info("Start download packages for new installation"))
        sql_version = self._get_result_mysql_version(sql_version)

        if sql_version == "auto" or sql_version.startswith("mysql80"):
            packages = [
                'cl-mysql80',
                'cl-mysql80-server',
                'cl-mysql80-server-core',
                'cl-mysql80-client',
                'cl-mysql80-client-core',
                'libmysqlclient21',
                'mysql-common'

            ]

        elif sql_version == "mariadb103":
            packages = [
                'cl-mariadb103-server',
                'cl-mariadb103-server-10.3',
                'cl-mariadb103-server-core-10.3',
                'cl-mariadb103-client',
                'cl-mariadb103-client-10.3',
                'cl-mariadb103-client-core-10.3',
                'cl-mariadb103-common',

            ]

        try:
            install_deb_from_url(CLOUDLINUX_RELEASE)
            exec_command('apt-get update -y')
        except Exception as err:
            print('err ->', err)
            exit(1)

        return packages

    def _load_new_packages(self, beta, sql_version=None, folder="new"):
        """Load new packages"""
        packages = self.get_new_packages(sql_version)

        if not download_apt_packages(packages, folder, disable_repos=False):
            self.ALL_PACKAGES_NEW_NOT_DOWNLOADED = True
        return packages

    @staticmethod
    def _check_mysql_version():
        """
        Retrieve MySQL version from mysql --version command
        :return: dictionary with version of form {
                short: two numbers of version (e.g. 5.5)
                extended: all numbers of version (e.g. 5.5.52)
                mysql_type: type flag (mysql or mariadb)
                full: mysql_type + short version (e.g. mariadb55)
            }
        """
        try:
            version_string = exec_command('mysql --version')
            version_info = re.findall(r'(?<=Distrib\s)[^,]+', version_string[0])
            if not version_info:
                # for mysql 8.0
                version_info = re.findall(r'(?<=Ver\s)\S+', version_string[0])
                parts = version_info[0].split('-')
            else:
                parts = version_info[0].split('-')

            version = {
                'short': '.'.join(parts[0].split('.')[:-1]),
                'extended': parts[0],
                'mysql_type': version_string[0].split(' ')[0] if len(version_string[0]) > 1 else 'mysql'
            }
            version.update({'full': '{m_type}{m_version}'.format(m_type=version['mysql_type'],
                                                                 m_version=version['short'].replace('.', ''))})
        except Exception:
            return {}
        return version

    def cleanup(self):
        """
        Cleanup downloaded packages and remove backup repo file
        """
        tmp_path = "%s/old" % DEB_TEMP_PATH

        if os.path.isdir(tmp_path):
            # first move previous downloaded packages to history folder
            history_path = os.path.join(self.HISTORY_FOLDER, "old.%s" %
                                        int(time.time()))
            shutil.move(tmp_path, history_path)

            self.my_cnf_manager('backup_old', history_path)

        if os.path.exists(DEB_TEMP_PATH):
            shutil.rmtree(DEB_TEMP_PATH)

        self.my_cnf_manager('cleanup')

        if os.path.exists("/etc/cron.d/dbgovernor-usermap-cron.bak"):
            os.unlink("/etc/cron.d/dbgovernor-usermap-cron.bak")

    def delete(self):
        """
        Delete governor packages
        """
        # first check config file
        check_file("/etc/my.cnf")

        # save current installed mysql version
        self._save_previous_version()

        # get list of installed packages
        installed_packages = self._load_current_packages()

        # remove cron file
        if os.path.exists("/etc/cron.d/dbgovernor-usermap-cron"):
            shutil.move("/etc/cron.d/dbgovernor-usermap-cron",
                        "/etc/cron.d/dbgovernor-usermap-cron.bak")

        # backup my.cnf file for restore if uninstall will be failed
        # if os.path.exists("/etc/my.cnf"):
        #     shutil.copy2("/etc/my.cnf", "/etc/my.cnf.govprev")
        self.my_cnf_manager('backup')

        # run trigger before governor uninstal
        self._before_delete()

        # run uninstall action
        self._delete(installed_packages)

        # run trigger after governor uninstall
        self._after_delete()
