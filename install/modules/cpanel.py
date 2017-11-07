# coding:utf-8
"""
This module contains class for managing governor on cPanel server
"""
from .base import InstallManager
from utilities import exec_command_out


class cPanelManager(InstallManager):
    """
    Installation manager for cPanel
    """

    def update_user_map_file(self):
        """
        Update user mapping file for cPanel
        """
        self._script("dbgovernor_map")

    @staticmethod
    def enable_mysql_monitor(enable=True):
        """
        Enable or disable mysql monitoring
        :param enable: if True - enable monitor
                       if False - disable monitor
        """
        exec_command_out(
            "whmapi1 configureservice service=mysql enabled=1 monitored={}".format(int(enable)))
