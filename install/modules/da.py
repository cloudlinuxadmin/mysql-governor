#coding:utf-8
"""
This module contains class for managing governor on DirectAdmin server
"""
import os
import sys
from utilities import grep, exec_command, bcolors
from .base import InstallManager


class DirectAdminManager(InstallManager):
    """
    Implementation for DA panel
    """
    CONF_FILE_MYSQL = "/usr/local/directadmin/conf/mysql.conf"
    CUSTOMBUILD = "/usr/local/directadmin/custombuild/build"

    def update_user_map_file(self):
        """
        Update user mapping file for cPanel
        """
        self._script("dbgovernor_map.py")

    def get_mysql_user(self):
        """
        Retrieve MySQL user name and password and save it into self attributes
        """
        if not os.path.exists(self.CONF_FILE_MYSQL):
            return None
        try:
            self.MYSQLUSER = grep(self.CONF_FILE_MYSQL, "user=")[0].split("=")[1]
            self.MYSQLPASSWORD = grep(self.CONF_FILE_MYSQL, "passwd=")[0].split("=")[1]
        except IndexError:
            pass

    def prepare_custombuild(self, version):
        """
        Update config file data for custombuild
        :param version: version to install
        """
        if version.startswith('mysql'):
            m_type = 'mysql'
        elif version.startswith('mariadb'):
            m_type = 'mariadb'
        else:
            print bcolors.fail('Unknown database requested!\nOnly official MySQL/MariDB supported')
            sys.exit(2)
        num = version.split(m_type)[-1]
        m_version = '{base}.{suffix}'.format(base=num[:-1],
                                             suffix=num[-1])
        exec_command('{custombuild} set {type} {ver}'.format(custombuild=self.CUSTOMBUILD, type=m_type, ver=m_version))
        exec_command('{custombuild} set mysql_inst {type}'.format(custombuild=self.CUSTOMBUILD, type=m_type))

    def install_packages(self):
        """
        Use custombuild script to install required version of MySQL/MariaDB
        If custombuild script fails, try once more to remove existing packages
        and then parent 'yum install' downloaded packages
        """
        print bcolors.info('Use custombuild script')
        res = exec_command('{custombuild} mysql'.format(custombuild=self.CUSTOMBUILD),
                           return_code=True)
        if res != 'yes':
            print bcolors.fail('custombuild script FAILED to install required MySQL/MariaDB version!')
            print bcolors.info('Try to install previously downloaded official packages')
            InstallManager.uninstall_mysql(self)
            InstallManager.install_packages(self)

    def uninstall_mysql(self):
        """
        Uninstall only our cl-* packages
        Other packages will be managed by custombuild script
        Remove official repository, installed for packages download
        :return:
        """
        if self.mysql_version['patched']:
            print bcolors.warning('cl-* packages detected, uninstalling...')
            InstallManager.uninstall_mysql(self)
        # delete created repo files
        try:
            os.unlink('/etc/yum.repos.d/MariaDB.repo')
            os.unlink('/etc/yum.repos.d/mysql-community.repo')
        except Exception:
            pass

    def give_new_pkg_info(self):
        """
        Tell user, that custombuild script will be used
        """
        print bcolors.info('CUSTOMBUILD SCRIPT WILL BE USED FOR NEW PACKAGES INSTALLATION')
        print bcolors.info('If custombuild script fails, these packages are going to be installed:\n\t--> {pkgs}'.format(pkgs='\n\t--> '.join(os.listdir(self.RPM_PATH))))

    def _before_install_mysql(self, version=None):
        """
        Actions, prior to MySQL/MariaDB installation process
        :return:
        """
        # stop mysql service
        InstallManager._before_install_mysql(self)
        # disable mysql monitoring
        print 'Deactivating mysql service'
        exec_command('{custombuild} set_service mysql OFF'.format(custombuild=self.CUSTOMBUILD))
        self.prepare_custombuild(version)

    def _after_install_mysql(self):
        """
        Actions after MySQL/MariaDB installation process
        :return:
        """
        # start mysql service
        InstallManager._after_install_mysql(self)
        # enable mysql monitoring
        print 'Activating mysql service'
        exec_command('{custombuild} set_service mysql ON'.format(custombuild=self.CUSTOMBUILD))
        print bcolors.warning("Don't forget to recompile PHP, please")
