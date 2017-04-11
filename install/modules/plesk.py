#coding:utf-8
"""
This module contains class for managing governor on Plesk server
"""
import os

from utilities import read_file
from .base import InstallManager


class PleskManager(InstallManager):
    """
    Implementation for plesk panel
    """
    DBPASS_PATH = "/etc/psa/.psa.shadow"

    def get_mysql_user(self):
        """
        Retrieve MySQL user name and password and save it into self attributes
        """
        if os.path.exists(self.DBPASS_PATH):
            self.MYSQLUSER = "admin"
            self.MYSQLPASSWORD = read_file(self.DBPASS_PATH)
