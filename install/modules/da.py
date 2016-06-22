#coding:utf-8
import os

from utilities import exec_command_out, check_file, grep, write_file, \
    read_file, remove_packages
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

    def _after_install_new_packages(self):
        """
        """
        if not os.path.exists(self.CONF_FILE_MYSQL):
            return None

        try:
            MYSQLUSER = grep(self.CONF_FILE_MYSQL, "user=")[0].split("=")[1]
            MYSQLPASSWORD = grep(self.CONF_FILE_MYSQL, "passwd=")[0].split("=")[1]
        except IndexError:
            pass
        else:
            self._set_mysql_access(MYSQLUSER, MYSQLPASSWORD)
            print "Rebuild php please... /usr/local/directadmin/custombuild/build php"

