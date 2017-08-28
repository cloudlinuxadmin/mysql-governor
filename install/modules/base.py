# coding:utf-8
"""
This module contains base class for managing governor on all supported
control panels
"""
import os
import sys
import re
import shutil

sys.path.append("../")

from utilities import get_cl_num, exec_command, exec_command_out, service, check_file, patch_governor_config


class InstallManager(object):
    """
    Base class with standard methods for any CP
    """
    # installation path
    SOURCE = "/usr/share/lve/dbgovernor/"
    PLUGIN_PATH = '/usr/share/lve/dbgovernor/plugins/governor.so-%(mysql_version)s'
    PLUGIN_DEST = '/usr/lib64/mysql/plugin/governor.so'
    MYSQLUSER = ''
    MYSQLPASSWORD = ''

    @staticmethod
    def factory(cp_name):
        """
        Get object instance for specific cp
        """
        if "cPanel" == cp_name:
            from .cpanel import cPanelManager
            return cPanelManager(cp_name)
        elif "DirectAdmin" == cp_name:
            from .da import DirectAdminManager
            return DirectAdminManager(cp_name)
        elif "Plesk" == cp_name:
            from .plesk import PleskManager
            return PleskManager(cp_name)
        elif "ISPManager" == cp_name:
            from .ispmanager import ISPMManager
            return ISPMManager(cp_name)
        elif "InterWorx" == cp_name:
            from .iworx import IWorxManager
            return IWorxManager(cp_name)
        else:
            return InstallManager(cp_name)

    cl_version = None
    cp_name = None

    def __init__(self, cp_name):
        self.cl_version = get_cl_num()
        self.cp_name = cp_name

    def install(self):
        """
        Governor plugin installation
        """
        if not self.cl_version:
            print "Unknown system type. Installation aborted"
            sys.exit(2)

        current_version = self._check_mysql_version()
        if not current_version:
            print 'No installed MySQL/MariaDB found'
        else:
            print '{} {} is installed here'.format(current_version['mysql_type'],
                                                   current_version['extended'])
            # copy corresponding plugin to mysql plugins' location
            governor_plugin = self.PLUGIN_PATH % {'mysql_version': current_version['full']}
            if os.path.exists(governor_plugin):
                print 'found file %s' % governor_plugin
                shutil.copy(governor_plugin, self.PLUGIN_DEST)

        return True

    def delete(self):
        """
        Delete governor
        """
        print 'This option is to delete governor package. Dummy for now'

    def update_user_map_file(self):
        """
        Update user mapping file.
        By default - empty
        """
        pass

    def get_mysql_user(self):
        """
        Retrieve MySQL user name and password and save it into self attributes
        """

    @staticmethod
    def _check_mysql_version():
        """
        Retrieve MySQL version from mysql --version command
        :return: dictionary with version of form {
                short: two numbers of version (e.g. 5.5)
                extended: all numbers of version (e.g. 5.5.52)
                mysql_type: type flag (mysql or mariadb)
                full: mysql_type + short version (e.g. mariadb55)
            }
        """
        try:
            version_string = exec_command('mysql --version')
            version_info = re.findall(r'(?<=Distrib\s)[^,]+', version_string[0])
            parts = version_info[0].split('-')
            version = {
                'short': '.'.join(parts[0].split('.')[:-1]),
                'extended': parts[0],
                'mysql_type': parts[1].lower() if len(parts) > 1 else 'mysql'
            }
            version.update({'full': '{m_type}{m_version}'.format(m_type=version['mysql_type'],
                                                                 m_version=version['short'].replace('.', ''))})
        except Exception:
            return {}
        return version

    def _set_mysql_access(self):
        """
        Set mysql admin login and password and save it to governor config
        """
        self.get_mysql_user()
        if self.MYSQLUSER and self.MYSQLPASSWORD:
            print "Patch governor configuration file"
            check_file("/etc/container/mysql-governor.xml")
            patch_governor_config(self.MYSQLUSER, self.MYSQLPASSWORD)

            if exec_command("rpm -qa governor-mysql", True):
                service("restart", "db_governor")
                print "DB-Governor restarted..."

    def _rel(self, path):
        """
        Get absolute path based on installed directory
        """
        return os.path.join(self.SOURCE, path)

    def rel(self, path):
        """
        Public wrapper for _rel
        """
        return self._rel(path)

    def _script(self, path, args=None):
        """
        Execute package script which locate in SOURCE directory
        """
        exec_command_out("%s %s" % (self._rel("scripts/%s" % path), args or ""))
