# coding:utf-8
"""
This module contains class for managing governor on ISPManager server
"""
import os

from utilities import exec_command, grep
from .base import InstallManager


class ISPMManager(InstallManager):
    """
    Implementation for ipsmanager panel
    """
    CONF_PATH = "/home/interworx/iworx.ini"

    def _after_install_new_packages(self):
        """
        Set mysql login and password
        """

        MYSQLUSER = "root"
        MYSQLPASSWORD = "Unknown"

        if os.path.exists("/usr/local/ispmgr/etc/ispmgr.conf"):
            MYSQLPASSWORD = exec_command(
                """cat /usr/local/ispmgr/etc/ispmgr.conf | sed -n '/DbServer "MySQL"/,/SupportCenterServer/p' | sed -n '/Password /p' | sed '/Change/d' | tr -d '\n' | cut -d" " -f2""",
                True, silent=True)
        elif os.path.exists("/usr/local/mgr5/etc/ispmgr.conf.d/db.conf"):
            try:
                MYSQLUSER = \
                grep("/usr/local/mgr5/etc/ispmgr.conf.d/db.conf", "DBUser")[
                    0].split(" ")[1].strip()
            except IndexError:
                MYSQLUSER = None

            try:
                MYSQLPASSWORD = \
                grep("/usr/local/mgr5/etc/ispmgr.conf.d/db.conf", "DBPassword")[
                    0].split(" ")[1].strip()
            except IndexError:
                MYSQLPASSWORD = None

        if MYSQLUSER and MYSQLPASSWORD:
            self._set_mysql_access(MYSQLUSER, MYSQLPASSWORD)

        print "The installation of MySQL for db_governor completed"
