# coding:utf-8
"""
This module contains base class for managing governor on all supported
control panels
"""
import os
import sys
import re
import shutil
import time
from distutils.version import LooseVersion

sys.path.append("../")

from utilities import get_cl_num, exec_command, exec_command_out, service, check_file, patch_governor_config


class InstallManager(object):
    """
    Base class with standard methods for any CP
    """
    # installation path
    SOURCE = "/usr/share/lve/dbgovernor/"
    PLUGIN_3 = '/usr/share/lve/dbgovernor/plugins/libgovernorplugin3.so'
    PLUGIN_4 = '/usr/share/lve/dbgovernor/plugins/libgovernorplugin4.so'
    PLUGIN_DEST = '%(plugin_path)sgovernor.so'
    MYSQLUSER = ''
    MYSQLPASSWORD = ''

    supported = {
        'mysql': '5.5.14',
        'mariadb': '5.5.37'
    }

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

        self._governorservice('stop')
        # try uninstalling old governor plugin
        try:
            print 'Try to uninstall old governor plugin...'
            self.mysql_command('uninstall plugin governor')
        except RuntimeError as e:
            print e
        self._mysqlservice('restart')

        current_version = self._check_mysql_version()
        if not current_version:
            print 'No installed MySQL/MariaDB found'
            print 'Cannot install plugin'
        else:
            print '{} {} is installed here'.format(current_version['mysql_type'],
                                                   current_version['extended'])
            if LooseVersion(current_version['extended']) < LooseVersion(self.supported[current_version['mysql_type']]):
                print "{t} {v} is unsupported by governor plugin. " \
                      "Support starts from {s}".format(t=current_version['mysql_type'],
                                                       v=current_version['extended'],
                                                       s=self.supported[current_version['mysql_type']])
                sys.exit(2)

            if self.check_patch():
                print 'This is PATCHED {}!'. format(current_version['mysql_type'])
                print 'Abort plugin installation'
            else:
                print 'Installing plugin...'
                # copy corresponding plugin to mysql plugins' location
                governor_plugin = self.PLUGIN_4 if self.plugin4(current_version) else self.PLUGIN_3
                if os.path.exists(governor_plugin):
                    # install plugin
                    print 'Selected file %s' % governor_plugin
                    _, plugin_path = self.mysql_command('select @@plugin_dir')
                    shutil.copy(governor_plugin, self.PLUGIN_DEST % {'plugin_path': plugin_path})
                    self.mysql_command('install plugin governor soname "governor.so"')
                    print 'Governor plugin installed successfully.'
        self._governorservice('start')
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
        try:
            with open('/etc/mysql_user') as user_data_file:
                self.MYSQLUSER, self.MYSQLPASSWORD = [l.strip() for l in user_data_file.readlines()]
        except IOError or OSError:
            pass

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

    def check_patch(self):
        """
        Determine if installed MySQL is patched
        :return: True if patched False otherwise
        """
        self.get_mysql_user()
        _, ver = self.mysql_command('select @@version')
        return 'cll-lve' in ver

    def plugin4(self, version_dict):
        """
        Should we set plugin of 4th version or not
        :return: True if plugin 4 is needed False otherwise
        """
        return version_dict['mysql_type'] == 'mysql' and LooseVersion(version_dict['extended']) >= LooseVersion('5.7.9')

    def mysql_command(self, command):
        """
        Execute mysql query via command line
        :param command: query to execute
        :return: result of query execution
        """
        if self.MYSQLUSER and self.MYSQLPASSWORD:
            result = exec_command("""mysql -u{user} -p{passwd} -e '{cmd};'""".format(user=self.MYSQLUSER,
                                                                                passwd=self.MYSQLPASSWORD,
                                                                                cmd=command))
        else:
            result = exec_command("""mysql -e '{cmd};'""".format(cmd=command))
        return result

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

    def _mysqlservice(self, action):
        """
        Manage mysql service
        """
        service(action, 'mysql')
        time.sleep(5)

    def _governorservice(self, action):
        """
        Manage db_governor service
        :param action:
        :return:
        """
        service(action, 'db_governor')
        time.sleep(5)
