# coding:utf-8
"""
This module contains class for managing governor on Iworx server
"""
import os

from utilities import grep
from .base import InstallManager


class IWorxManager(InstallManager):
    """
    Implementation for iworx panel
    """
    CONF_PATH = "/home/interworx/iworx.ini"

    def _after_install_new_packages(self):
        """
        Set mysql login and password
        """
        MYSQLUSER = "iworx"
        if not os.path.exists(self.CONF_PATH):
            return

        lines = grep(self.CONF_PATH, "rootdsn=")
        try:
            # MYSQLPASSWORD = exec_command("cat /home/interworx/iworx.ini | grep rootdsn= | cut -d"/" -f3 | cut -d: -f2 | cut -d@ -f1", True)
            MYSQLPASSWORD = lines[0].split("/")[2].split(":")[1].split("@")[0]
        except IndexError:
            MYSQLPASSWORD = None

        if MYSQLPASSWORD:
            self._set_mysql_access(MYSQLUSER, MYSQLPASSWORD)

        print "The installation of MySQL for db_governor completed"
