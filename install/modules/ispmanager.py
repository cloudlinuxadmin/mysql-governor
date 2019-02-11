# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
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

    def get_mysql_user(self):
        """
        Retrieve MySQL user name and password and save it into self attributes
        """
        self.MYSQLUSER = "root"
        self.MYSQLPASSWORD = "Unknown"

        if os.path.exists("/usr/local/ispmgr/etc/ispmgr.conf"):
            self.MYSQLPASSWORD = exec_command(
                """cat /usr/local/ispmgr/etc/ispmgr.conf | sed -n '/DbServer "MySQL"/,/SupportCenterServer/p' | sed -n '/Password /p' | sed '/Change/d' | tr -d '\n' | cut -d" " -f2""",
                True, silent=True)
        elif os.path.exists("/usr/local/mgr5/etc/ispmgr.conf.d/db.conf"):
            try:
                self.MYSQLUSER = \
                    grep("/usr/local/mgr5/etc/ispmgr.conf.d/db.conf", "DBUser")[
                        0].split(" ")[1].strip()
            except IndexError:
                self.MYSQLUSER = None

            try:
                self.MYSQLPASSWORD = \
                    grep("/usr/local/mgr5/etc/ispmgr.conf.d/db.conf", "DBPassword")[
                        0].split(" ")[1].strip()
            except IndexError:
                self.MYSQLPASSWORD = None
