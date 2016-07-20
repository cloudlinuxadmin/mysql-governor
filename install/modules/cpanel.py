#coding:utf-8
import os
import shutil

from utilities import exec_command_out, grep, add_line, \
    service, remove_lines, write_file, replace_lines, touch, \
    is_package_installed, remove_packages, exec_command, parse_rpm_name
from .base import InstallManager


class cPanelManager(InstallManager):
    """
    Installation manager for cPanel
    """

    def update_user_map_file(self):
        """
        Update user mapping file for cPanel
        """
        self._script("dbgovernor_map")

    def install_mysql_beta_testing_hooks(self):
        """
        """
        self._set_fs_suid_dumpable()
        self._script("cpanel-install-hooks")

    def fix_cl7_mysql(self):
        """
        """
        if 7 == self.cl_version:
            if os.path.lexists("/etc/init.d/mysqld"):
                os.remove("/etc/init.d/mysqld")
            if os.path.lexists("/etc/rc.d/init.d/mysqld"):
                os.remove("/etc/rc.d/init.d/mysqld")

    def _delete(self, installed_packages):
        """
        """
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

        # TODO: for what?
        # exec_command_out(SOURCE+"cpanel/install-db-governor-uninstall")
        
        service("stop", "mysql")
        # remove governor package
        exec_command_out("rpm -e governor-mysql")
        # delete installed packages
        remove_packages(installed_packages)

        exec_command_out("/scripts/upcp --force")

        if os.path.exists("/scripts/check_cpanel_rpms"):
            exec_command_out("/scripts/check_cpanel_rpms --fix --targets="
                             "MySQL50,MySQL51,MySQL55,MySQL56,MariaDB,MariaDB100,MariaDB101")

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
            if os.path.exists("/usr/local/cpanel/scripts/update_local_rpm_versions"):
                if not os.path.exists("/var/cpanel/rpm.versions.d/cloudlinux.versions"):
                    shutil.copy2(self._rel("utils/cloudlinux.versions"),
                                 "/var/cpanel/rpm.versions.d/cloudlinux.versions")
            else:
                if not os.path.exists("/etc/cpupdate.conf.governor"):
                    self._get_mysqlup()
                touch("/etc/mysqlupdisable")

        self._script("cpanel-install-hooks")

        if os.path.exists("/usr/local/cpanel/cpanel") and \
                os.path.exists("/usr/local/cpanel/scripts/update_local_rpm_versions"):
            if os.path.exists("/etc/mysqlupdisable"):
                os.unlink("/etc/mysqlupdisable")
            remove_lines("/etc/cpupdate.conf", "MYSQLUP=never")

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
        """

    def _get_mysqlup(self):
        """
        ? Set value for panel update MYSQLUP option
        """
        if os.path.exists("/etc/cpupdate.conf"):
            shutil.copy2("/etc/cpupdate.conf", "/etc/cpupdate.conf.governor")
            is_mysqlup = grep("/etc/cpupdate.conf", "MYSQLUP")
            if is_mysqlup:
                if not grep(is_mysqlup, "never$", True):
                    replace_lines("/etc/cpupdate.conf", "".join(is_mysqlup), "MYSQLUP=never")
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
            mysqlname_array = exec_command(self._rel("scripts/detect-cpanel-mysql-version.pm"))
            mysqlname = ""
            if len(mysqlname_array)>0:
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
        if len(result)==4:
            return exec_command(self._rel("scripts/cpanel-mysql-url-detect.pm %s %s-%s" % (result[0], result[1], result[2])), True)
        return ""
