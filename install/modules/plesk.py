#coding:utf-8
import os

from utilities import read_file
from .base import InstallManager


class PleskManager(InstallManager):
    """
    Implementation for plesk panel
    """
    DBPASS_PATH = "/etc/psa/.psa.shadow"

    def _after_install_new_packages(self):
        """
        Set mysql login and password
        """
        MYSQLUSER = "admin"
        MYSQLPASSWORD = None
        if os.path.exists(self.DBPASS_PATH):
            MYSQLPASSWORD = read_file(self.DBPASS_PATH)

        if MYSQLPASSWORD:
            self._set_mysql_access(MYSQLUSER, MYSQLPASSWORD)

        print "The installation of MySQL for db_governor completed"
