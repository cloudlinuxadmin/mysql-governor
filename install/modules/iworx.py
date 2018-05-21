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

    def get_mysql_user(self):
        """
        Retrieve MySQL user name and password and save it into self attributes
        """
        if os.path.exists(self.CONF_PATH):
            self.MYSQLUSER = "iworx"
            lines = grep(self.CONF_PATH, "rootdsn=")
            try:
                # MYSQLPASSWORD = exec_command("cat /home/interworx/iworx.ini | grep rootdsn= | cut -d"/" -f3 | cut -d: -f2 | cut -d@ -f1", True)
                self.MYSQLPASSWORD = lines[0].split("/")[2].split(":")[1].split("@")[0]
            except IndexError:
                self.MYSQLPASSWORD = None
