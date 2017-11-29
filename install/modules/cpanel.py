# coding:utf-8
"""
This module contains class for managing governor on cPanel server
"""
import os
from .base import InstallManager
from utilities import exec_command_out, exec_command, bcolors


class cPanelManager(InstallManager):
    """
    Installation manager for cPanel
    """

    targets = {
        'mysql55': 'MySQL55',
        'mysql56': 'MySQL56',
        'mariadb100': 'MariaDB100',
        'mariadb101': 'MariaDB101',
        'mariadb102': 'MariaDB102',
    }
    migration_table = {
        'mysql55': ('mysql56',),
        'mysql56': ('mysql57', 'mariadb100'),
        'mysql57': (),
        'mariadb55': ('mysql56', 'mariadb100'),
        'mariadb100': ('mysql56', 'mariadb101'),
        'mariadb101': ('mariadb102', ),
        'mariadb102': ()
    }

    def __init__(self, cp_name):
        InstallManager.__init__(self, cp_name)
        self.legacy_rpms = False

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

    def is_migration_possible(self, new_version):
        """
        Extend method with detection of legacy RPMs to be installed
        :param new_version: version to install
        """
        # detect cPanel's legacy RPMS
        if new_version in ('mysql55', 'mysql56'):
            print bcolors.info('Legacy RPMs requested for install')
            self.legacy_rpms = True
        # check migration possibilities
        return InstallManager.is_migration_possible(self, new_version)

    def install_packages(self):
        """
        Use check_cpanel_rpms or base procedure
        """
        if self.legacy_rpms:
            print bcolors.info('Use check_cpanel_rpms script')
            res = exec_command('/usr/local/cpanel/scripts/check_cpanel_rpms --fix --targets={}'.format(','.join(self.targets.values())),
                               return_code=True)
            if res != 'yes':
                print bcolors.fail('check_cpanel_rpms script FAILED to install required MySQL/MariaDB version!')
                print bcolors.warning('Try to install previously downloaded official packages')
                self.rpm_management('unmanaged')
                InstallManager.install_packages(self)
            else:
                print bcolors.ok('Legacy RPMs installed!')
                # delete created repo files
                self.delete_repos()
        else:
            InstallManager.install_packages(self)

    def give_new_pkg_info(self):
        """
        Tell user, what scheme will be used
        """
        if self.legacy_rpms:
            print bcolors.info("CPANEL'S LEGACY RPMS WILL BE INSTALLED USING /usr/local/cpanel/scripts/check_cpanel_rpms --fix")
            print bcolors.info('If check_cpanel_rpms script fails, these packages are going to be installed:\n\t--> {pkgs}'.format(pkgs='\n\t--> '.join(os.listdir(self.RPM_PATH))))
        else:
            InstallManager.give_new_pkg_info(self)

    def rpm_management(self, action, target=None):
        """
        Switch cPanel's RPM management with update_local_rpm_versions script
        :param action: installed|uninstalled|unmanaged
        :param target: rpm target or all targets if None
        """
        valid_actions = ('installed', 'uninstalled', 'unmanaged')
        if action not in valid_actions:
            raise RuntimeError('unknown action for RPM management: {}'.format(action))

        manage_command = '/usr/local/cpanel/scripts/update_local_rpm_versions --edit target_settings.%(target)s %(action)s'
        if not target:
            # apply given action to all known targets
            print bcolors.info('{} management for all known RPMS'.format(action))
            for t in self.targets.values():
                exec_command(manage_command % {'target': t, 'action': action})
        else:
            print bcolors.info('{} management for {}'.format(action, target))
            # apply given action to given target
            t = self.targets.get(target)
            if not t:
                raise RuntimeError('unknown target for RPM management: {}'.format(target))
            exec_command(manage_command % {'target': t, 'action': action})

    def restore_default_rpm_management(self):
        """
        Clear target settings for MariaDB from local.versions file
        """
        manage_command = '/usr/local/cpanel/scripts/update_local_rpm_versions --del target_settings.%(target)s'
        mariadb_targets = filter(lambda x: 'MariaDB' in x, self.targets.values())
        for t in mariadb_targets:
            exec_command(manage_command % {'target': t})

    def _before_install_mysql(self, version=None):
        """
        Actions, prior to MySQL/MariaDB installation process
        """
        # stop mysql service
        InstallManager._before_install_mysql(self)
        # disable mysql monitoring
        print 'Deactivating mysql monitoring'
        self.enable_mysql_monitor(False)
        # set all known targets to uninstalled
        self.rpm_management('uninstalled')
        # set new version to installed if applicable
        if self.legacy_rpms:
            self.rpm_management('installed', version)

    def _after_install_mysql(self):
        """
        Actions after MySQL/MariaDB installation process
        """
        # delete files with version cache
        try:
            os.unlink('/var/cpanel/mysql_server_version_cache')
            os.unlink('/var/lib/mysql/mysql_upgrade_info')
        except Exception:
            pass
        # drop rpm management for mariadb to default state
        self.restore_default_rpm_management()
        # clear cloudlinux.versions remained from governor 1.2
        if os.path.exists('/var/cpanel/rpm.versions.d/cloudlinux.versions'):
            os.unlink('/var/cpanel/rpm.versions.d/cloudlinux.versions')
        # start mysql service
        InstallManager._after_install_mysql(self)
        # enable mysql monitoring
        print 'Activating mysql monitoring'
        self.enable_mysql_monitor()
