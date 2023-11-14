#coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
"""
This module contains class for managing governor on DirectAdmin server
"""
import os
import shutil
from glob import glob

from utilities import (
    check_file,
    exec_command,
    exec_command_out,
    grep,
    read_file,
    remove_packages,
    write_file,
)

from .base import InstallManager


class DirectAdminManager(InstallManager):
    """
    Implementation for DA panel
    """
    CONF_FILE_MYSQL = "/usr/local/directadmin/conf/mysql.conf"

    def update_user_map_file(self):
        """
        Update user mapping file for cPanel
        """
        self._script("dbgovernor_map.py")

    def _delete(self, installed_packages):
        """
        Remove installed packages
        """
        check_file("/usr/local/directadmin/custombuild/build")

        print("Removing mysql for db_governor start")

        self._mysqlservice("stop")
        # remove governor package
        exec_command_out("rpm -e governor-mysql")
        # delete installed packages
        remove_packages(installed_packages)

        param = "mysql"
        if os.path.exists("/usr/share/lve/dbgovernor/da.tp.old"):
            param = read_file("/usr/share/lve/dbgovernor/da.tp.old")

        exec_command_out(f"/usr/local/directadmin/custombuild/build set mysql_inst {param}")
        exec_command_out("/usr/local/directadmin/custombuild/build mysql update")

        print("Removing mysql for db_governor completed")

    def _before_install_new_packages(self):
        """
        Specific actions before new packages installation
        """
        print("The installation of MySQL for db_governor has started")

        check_file("/usr/local/directadmin/custombuild/build")
        check_file("/usr/local/directadmin/custombuild/options.conf")

        # MYSQL_DA_TYPE=`cat /usr/local/directadmin/custombuild/options.conf | grep mysql_inst= | cut -d= -f2`
        try:
            MYSQL_DA_TYPE = grep("/usr/local/directadmin/custombuild/options.conf", "mysql_inst=")[0].split("=")[1]
        except IndexError:
            MYSQL_DA_TYPE = ""

        if os.path.exists("/usr/share/lve/dbgovernor/da.tp.old"):
            if MYSQL_DA_TYPE == "no":
                MYSQL_DA_TYPE = read_file("/usr/share/lve/dbgovernor/da.tp.old")
            else:
                write_file("/usr/share/lve/dbgovernor/da.tp.old", MYSQL_DA_TYPE)
        else:
            write_file("/usr/share/lve/dbgovernor/da.tp.old", MYSQL_DA_TYPE)

        exec_command_out("/usr/local/directadmin/custombuild/build set mysql_inst no")

        self._mysqlservice("stop")

    def get_mysql_user(self):
        """
        Retrieve MySQL user name and password and save it into self attributes
        """
        if not os.path.exists(self.CONF_FILE_MYSQL):
            return None
        try:
            self.MYSQLUSER = grep(self.CONF_FILE_MYSQL, "user=")[0].split("=")[1]
            self.MYSQLPASSWORD = grep(self.CONF_FILE_MYSQL, "passwd=")[0].split("=")[1]
        except IndexError:
            pass

    def _after_install_new_packages(self):
        """
        Specific actions after new packages installation
        """
        # call parent after_install
        InstallManager._after_install_new_packages(self)
        # install MySQL-python module
        exec_command("yum install -y alt-python37-MySQL-meta --disableexcludes=all")
        print("Rebuild php please... /usr/local/directadmin/custombuild/build php")

    def _detect_version_if_auto(self):
        """
        Detect vesrion of MySQL if mysql.type is auto
        """
        print("Detecting MySQL version for AUTO")

        try:
            MYSQL_DA_VER = self.prev_version['full']
            print(f'Detected successfully from installed mysql binary: {MYSQL_DA_VER}')
        except KeyError:
            print('Failed to detect from mysql binary, trying to detect from custombuild options')
            check_file("/usr/local/directadmin/custombuild/build")
            check_file("/usr/local/directadmin/custombuild/options.conf")
            # MYSQL_DA_TYPE=`cat /usr/local/directadmin/custombuild/options.conf | grep mysql_inst= | cut -d= -f2`
            try:
                mysql_ver_grep = grep("/usr/local/directadmin/custombuild/options.conf", "mysql=")
                MYSQL_DA_VER = mysql_ver_grep[0].split("=")[1].strip()
                mysql_type_grep = grep("/usr/local/directadmin/custombuild/options.conf", "mysql_inst=")
                MYSQL_DA_TYPE = mysql_type_grep[0].split("=")[1].strip()
            except IndexError:
                MYSQL_DA_VER = ""
                MYSQL_DA_TYPE = ""

            if MYSQL_DA_TYPE == "no":
                if os.path.exists("/usr/share/lve/dbgovernor/da.tp.old"):
                    MYSQL_DA_TYPE = read_file("/usr/share/lve/dbgovernor/da.tp.old")
                elif os.path.exists("/usr/bin/mysql"):
                    result = exec_command("/usr/bin/mysql -V | grep -c 'MariaDB' -i || true", True)
                    if result == "0":
                        MYSQL_DA_TYPE = "mysql"
                    else:
                        MYSQL_DA_TYPE = "mariadb"

            print("I got %s and %s" % (MYSQL_DA_VER, MYSQL_DA_TYPE))

            mysql_version_map = {
                "5.0": "mysql50",
                "5.1": "mysql51",
                "5.5": "mysql55",
                "5.6": "mysql56",
                "5.7": "mysql57",
                "8.0": "mysql80",
                "10.0.0": "mariadb100",
                "10.1.1": "mariadb101"
            }
            mariadb_version_map = {
                "10.11": "mariadb1011",
                "10.6": "mariadb106",
                "10.5": "mariadb105",
                "10.4": "mariadb104",
                "10.3": "mariadb103",
                "10.2": "mariadb102",
                "10.1": "mariadb101",
                "10.0": "mariadb100",
                "5.6": "mariadb100",
                "5.5": "mariadb100",
                "10.0.0": "mariadb100",
                "10.1.1": "mariadb101"
            }

            if MYSQL_DA_TYPE == "mysql":
                MYSQL_DA_VER = mysql_version_map[MYSQL_DA_VER]
            elif MYSQL_DA_TYPE == "mariadb":
                MYSQL_DA_VER = mariadb_version_map[MYSQL_DA_VER]

        return MYSQL_DA_VER

    def _custom_download_of_rpm(self, package_name):
        """
        How we should to download installed MySQL package
        There could be a lot of packages in /usr/local/directadmin/custombuild/mysql,
        not all of them relevant (installed) or fine ones (not corrupted)
        """
        if package_name == "+":
            return "yes"

        bad_pkg = False
        list_of_rpm = glob("/usr/local/directadmin/custombuild/mysql/*.rpm") + glob(
            "/usr/local/directadmin/scripts/packages/*.rpm")
        for found_package in list_of_rpm:
            try:
                result = exec_command(f"/bin/rpm -qp {found_package}", True)
                if package_name in result:
                    pkg_name_real = found_package
                    if pkg_name_real != "" and os.path.exists(pkg_name_real):
                        return f"file:{pkg_name_real}"
            except RuntimeError as e:
                print(f"Failed to query package {found_package}: {e}\n")
                bad_pkg = True

        if bad_pkg:
            return f"bad_file:{package_name}"
        else:
            return ""

    def _custom_rpm_installer(self, package_name, indicator=False):
        """
        Specific package installer
        :param package_name:
        :param indicator:
        :return:
        """
        if not indicator:
            exec_command_out(f"/bin/rpm -ihv --force --nodeps {package_name}")
            return ""
        else:
            return "yes"

    def fix_mysqld_service(self):
        """
        Restore mysqld.service
        """
        try:
            shutil.copy(self._rel("scripts/mysqld.service"),
                        '/usr/local/directadmin/custombuild/configure/systemd/mysqld.service')
            print('mysqld.service restored!')
        except Exception:
            print('ERROR occurred while attempting to restore mysqld.service!')
