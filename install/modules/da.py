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

from utilities import exec_command_out, check_file, grep, write_file, \
    read_file, remove_packages, exec_command
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

        print "Removing mysql for db_governor start"

        self._mysqlservice("stop")
        # remove governor package
        exec_command_out("rpm -e governor-mysql")
        # delete installed packages
        remove_packages(installed_packages)

        param = "mysql"
        if os.path.exists("/usr/share/lve/dbgovernor/da.tp.old"):
            param = read_file("/usr/share/lve/dbgovernor/da.tp.old")

        exec_command_out("/usr/local/directadmin/custombuild/build set mysql_inst %s" % param)
        exec_command_out("/usr/local/directadmin/custombuild/build mysql update")

        print "Removing mysql for db_governor completed"

    def _before_install_new_packages(self):
        """
        Specific actions before new packages installation
        """
        print "The installation of MySQL for db_governor has started"

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
        exec_command("yum install -y MySQL-python --disableexcludes=all")
        print "Rebuild php please... /usr/local/directadmin/custombuild/build php"

    def _detect_version_if_auto(self):
        """
        Detect vesrion of MySQL if mysql.type is auto
        """
        print "Detect MySQL version for AUTO"

        check_file("/usr/local/directadmin/custombuild/build")
        check_file("/usr/local/directadmin/custombuild/options.conf")
        MYSQL_DA_VER = ""

        # MYSQL_DA_TYPE=`cat /usr/local/directadmin/custombuild/options.conf | grep mysql_inst= | cut -d= -f2`
        try:
            MYSQL_DA_VER = grep("/usr/local/directadmin/custombuild/options.conf", "mysql=")[0].split("=")[1].strip()
            MYSQL_DA_TYPE = grep("/usr/local/directadmin/custombuild/options.conf", "mysql_inst=")[0].split("=")[1].strip()
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

        print "I got %s and %s" % (MYSQL_DA_VER, MYSQL_DA_TYPE)

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
            "10.3": "mariadb103",
            "10.2": "mariadb102",
            "10.1": "mariadb101",
            "10.0": "mariadb100",
            "5.6": "mariadb100",
            "5.5": "mariadb100",
            "10.0.0": "mariadb100",
            "10.1.1": "mariadb100"
        }

        if MYSQL_DA_TYPE == "mysql":
            MYSQL_DA_VER = mysql_version_map[MYSQL_DA_VER]
        elif MYSQL_DA_TYPE == "mariadb":
            MYSQL_DA_VER = mariadb_version_map[MYSQL_DA_VER]

        return MYSQL_DA_VER

    def _custom_download_of_rpm(self, package_name):
        """
        How we should to download installed MySQL package
        """
        if package_name == "+":
            return "yes"

        pkg_name_real = ""
        list_of_rpm = glob("/usr/local/directadmin/custombuild/mysql/*.rpm")
        for found_package in list_of_rpm:
            result = exec_command("/bin/rpm -qp %s" % found_package, True)
            if package_name in result:
                pkg_name_real = found_package
                break

        if pkg_name_real != "" and os.path.exists(pkg_name_real):
            return "file:%s" % pkg_name_real

        return ""

    def _custom_rpm_installer(self, package_name, indicator=False):
        """
        Specific package installer
        :param package_name:
        :param indicator:
        :return:
        """
        if not indicator:
            exec_command_out("/bin/rpm --ihv --force --nodeps %s" % package_name)
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
            print 'mysqld.service restored!'
        except Exception:
            print 'ERROR occurred while attempt to restore mysqld.service!'
