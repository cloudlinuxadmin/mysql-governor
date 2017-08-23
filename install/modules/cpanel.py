# coding:utf-8
"""
This module contains class for managing governor on cPanel server
"""
from .base import InstallManager


class cPanelManager(InstallManager):
    """
    Installation manager for cPanel
    """

    def update_user_map_file(self):
        """
        Update user mapping file for cPanel
        """
        self._script("dbgovernor_map")
