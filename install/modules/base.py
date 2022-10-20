# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
"""
This module contains base class for managing governor on all supported
control panels
"""
import os
import stat
import shutil
import sys
import time
import urllib.request, urllib.error, urllib.parse
import pwd
import grp
import re
from datetime import datetime

sys.path.append("../")

from utilities import get_cl_num, exec_command, exec_command_out, new_lve_ctl, \
    num_proc, grep, add_line, service, install_packages, touch, \
    remove_packages, read_file, download_packages, write_file, RPM_TEMP_PATH, \
    is_package_installed, check_file, mysql_version, \
    confirm_packages_installation, create_mysqld_link, \
    correct_mysqld_service_for_cl7, \
    correct_remove_notowned_mysql_service_names_cl7, \
    correct_remove_notowned_mysql_service_names_not_symlynks_cl7, get_mysql_log_file, \
    check_mysqld_is_alive, makedir_recursive, patch_governor_config, bcolors, force_update_cagefs, \
    show_new_packages_info, wizard_install_confirm, rewrite_file, cl8_module_enable, debug_log, \
    read_config_file, mycnf_writable, IS_UBUNTU, install_deb_packages, get_mysql_cnf_value, get_section_from_all_cnfs


class InstallManager:
    """
    Base class with standard methods for any CP
    """
    # installation path
    SOURCE = "/usr/share/lve/dbgovernor/"
    # file with new version for install
    NEW_VERSION_FILE = "/usr/share/lve/dbgovernor/mysql.type"
    # file with cached installed version before install
    CACHE_VERSION_FILE = "/usr/share/lve/dbgovernor/mysql.type.installed"
    # file with cached CL8 module stream before install
    CACHE_MODULE_FILE = "/usr/share/lve/dbgovernor/cl8_module.saved"
    HISTORY_FOLDER = "/usr/share/lve/dbgovernor/history"
    REPO_NAMES = {
        "mysql51": "mysql-5.1",
        "mysql55": "mysql-5.5",
        "mysql56": "mysql-5.6",
        "mysql57": "mysql-5.7",
        "mysql80": "mysql-8.0",
        "mariadb55": "mariadb-5.5",
        "mariadb100": "mariadb-10.0",
        "mariadb101": "mariadb-10.1",
        "mariadb102": "mariadb-10.2",
        "mariadb103": "mariadb-10.3",
        "mariadb104": "mariadb-10.4",
        "mariadb105": "mariadb-10.5",
        "mariadb106": "mariadb-10.6",
# We still don't support MariaDB 10.7, 10.8 and 10.9 and possibly won't do it.
#        "mariadb107": "mariadb-10.7",
        "percona56": "percona-5.6"
    }
    MODULE_STREAMS = {
        "mysql55": "mysql:cl-MySQL55",
        "mysql56": "mysql:cl-MySQL56",
        "mysql57": "mysql:cl-MySQL57",
        "mysql80": "mysql:cl-MySQL80",
        "mariadb55": "mariadb:cl-MariaDB55",
        "mariadb100": "mariadb:cl-MariaDB100",
        "mariadb101": "mariadb:cl-MariaDB101",
        "mariadb102": "mariadb:cl-MariaDB102",
        "mariadb103": "mariadb:cl-MariaDB103",
        "mariadb104": "mariadb:cl-MariaDB104",
        "mariadb105": "mariadb:cl-MariaDB105",
        "mariadb106": "mariadb:cl-MariaDB106",
# We still don't support MariaDB 10.7, 10.8 and 10.9 and possibly won't do it.
#        "mariadb107": "mariadb:cl-MariaDB107",
        "percona56": "percona:cl-Percona56",
        "auto": "mysql:8.0"
    }
    ALL_PACKAGES_NEW_NOT_DOWNLOADED = False
    ALL_PACKAGES_OLD_NOT_DOWNLOADED = False
    DISABLED = False
    ROLLBACK = False
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
    _old_packages = None
    _new_packages = None

    def __init__(self, cp_name):
        self.cl_version = get_cl_num()
        self.cp_name = cp_name

        # In case of custom database my.cnf file can be located in some nonstandard path.
        # That's why we try to get it from os environ
        self.my_cnf_path = '/etc/my.cnf'
        self.VAR_LIB_MYSQL = '/var/lib/mysql'
        self.my_cnf_datadir = get_section_from_all_cnfs('datadir')
        print('Database datadir: ', self.my_cnf_datadir)

    @staticmethod
    def my_cnf_manager(action, old_path=None):
        """
        Allows to manage known manipulations with /etc/my.cnf file
        :param action: action to perform
        :param old_path: path to my.cnf if needed
        """
        # fix for packages without /etc/my.cnf file
        if action == 'touch':
            if mycnf_writable():
                touch("/etc/my.cnf")
            return

        actions = {
            'backup': lambda x: shutil.copy2(x, "/etc/my.cnf.govprev"),
            'restore': lambda x: shutil.move(x, "/etc/my.cnf"),
            'restore_old': lambda x: shutil.copy(x, "/etc/my.cnf"),
            'restore_rpmsave': lambda x: shutil.copy2(x, "/etc/my.cnf"),
            'cleanup': lambda x: os.unlink(x),
            'backup_old': '',
            'backup_my_cnf_d': lambda x: shutil.copytree(x, "/etc/my.cnf.d.govprev")
        }

        if action not in actions.keys():
            raise RuntimeError('Cannot manage /etc/my.cnf: '
                               'unknown action %s' % action)

        if action == 'backup_my_cnf_d':
            my_cnf_d_path = '/etc/my.cnf.d'
            if os.path.exists(my_cnf_d_path):
                actions.get(action)(my_cnf_d_path)
                return

        if action == 'backup':
            working_path = "/etc/my.cnf"
        elif action == 'restore_old':
            working_path = "%s/my.cnf" % old_path
        else:
            working_path = "/etc/my.cnf.govprev"

        if os.path.exists(working_path):
            try:
                if action == 'backup_old':
                    shutil.move(working_path, "%s/my.cnf" % old_path)
                else:
                    actions.get(action)(working_path)
            except PermissionError as e:
                print(f'Unable to perform actions on the my.cnf : {e}')

    def my_cnf_inspect(self):
        """
        Fix nonexistent paths to log-error and pid-file
        """
        track = {
            'files': ('log-error', ),
            'paths': ('pid-file', )
        }
        default_log = f'{self.my_cnf_datadir}/mysqld.error.log'
        default_pid = f'{self.my_cnf_datadir}/mysqld.pid'

        conf = read_config_file('/etc/my.cnf')
        # try to find non-existent paths, defined in /etc/my.cnf
        for s in conf.sections():
            for opt, val in conf.items(s):
                if opt in track['files']:
                    # inspect whole path
                    if not os.path.exists(val):
                        print('NO LOG for {opt} --> {v}'.format(opt=opt, v=val))
                        conf.set(s, opt, default_log)
                elif opt in track['paths']:
                    # inspect dir path
                    if not os.path.exists(os.path.dirname(val)):
                        print('NO PATH for {opt} --> {v}'.format(opt=opt, v=val))
                        conf.set(s, opt, default_pid)

        if self._get_new_version() == 'mysql80':
            # for mysql80 set old authentication plugin as default one
            # in order to prevent php connection errors
            # MYSQLG-297, MySQLG-301
            if not conf.has_section('mysqld'):
                conf.add_section('mysqld')
            conf.set('mysqld', 'default-authentication-plugin', 'mysql_native_password')

        if mycnf_writable() and conf.sections():
            with open('/etc/my.cnf', 'w') as configfile:
                conf.write(configfile)

    def remove_current_packages(self):
        """
        Delete current installed packages
        """
        # stop mysql service
        self._mysqlservice("stop")
        # disable service for CL7 to eliminate broken symlinks after removing
        if self.cl_version >= 7:
            self._mysqlservice("disable")

        # remove current mysql packages
        remove_packages(self._old_packages)

    def install(self, beta, no_confirm, wizard_mode):
        """
        Install stable or beta packages
        @param `beta` bool: install beta or production
        @param `path` str: path to packages for install
        """
        if not self.cl_version:
            print("Unknown system type. Installation aborted")
            sys.exit(1)

        self._before_install()

        # remember installed mysql version
        self.prev_version = self._check_mysql_version()

        # first download packages for current and new mysql versions
        self._load_packages(beta)

        # save current installed mysql version
        self._save_previous_version()

        if self.ALL_PACKAGES_NEW_NOT_DOWNLOADED:
            self.print_warning_about_not_complete_of_newpkg_saving()
            return False

        if self.ALL_PACKAGES_OLD_NOT_DOWNLOADED:
            self.print_warning_about_not_complete_of_pkg_saving()

        new_version = show_new_packages_info("new")

        if wizard_mode:
            # wizard mode has its own confirmation logic
            if not wizard_install_confirm(new_version, self.prev_version):
                self.cl8_enable_cached()
                sys.exit(3)
        elif not confirm_packages_installation(new_version,
                                               self.prev_version,
                                               no_confirm):
            self.DISABLED = True
            self.cl8_enable_cached()
            return False

        # if os.path.exists("/etc/my.cnf"):
        #     shutil.copy2("/etc/my.cnf", "/etc/my.cnf.govprev")
        self.my_cnf_manager('backup_my_cnf_d')
        self.my_cnf_manager('backup')

        create_mysqld_link("mysqld", "mysql")
        create_mysqld_link("mysql", "mysqld")

        # first remove installed mysql packages
        self.remove_current_packages()

        correct_remove_notowned_mysql_service_names_cl7()
        correct_remove_notowned_mysql_service_names_not_symlynks_cl7()

        # restore my.cnf, because before removing packages, we make backup of /etc/my.cnf and  /etc/my.cnf.d/* to *.govprev extension
        # if os.path.exists("/etc/my.cnf.govprev"):
        #     shutil.copy2("/etc/my.cnf.govprev", "/etc/my.cnf")
        self.my_cnf_manager('restore_rpmsave')

        self.set_fs_suid_dumpable()
        self._check_leave_pid()

        self._before_install_new_packages()

        # don`t know for what this
        self._kill_mysql()

        try:
            # new db version which will be installing
            if not install_packages("new", beta):
                # if not install new packages - don`t do next actions
                return False
        except RuntimeError:
            return False

        create_mysqld_link("mysqld", "mysql")
        create_mysqld_link("mysql", "mysqld")

        correct_mysqld_service_for_cl7(self._get_result_mysql_version(None))

        # fix for packages without /etc/my.cnf file
        # if not os.path.exists("/etc/my.cnf"):
        #     touch("/etc/my.cnf")
        self.my_cnf_manager('touch')

        # check if log MySQL's log file exists and correct perms
        # in other case MySQL will not starts
        log_file = get_mysql_log_file()
        makedir_recursive(log_file)
        touch(log_file)
        log_owner_name = pwd.getpwuid(os.stat(log_file).st_uid)[0]
        log_owner_grp = grp.getgrgid(os.stat(log_file).st_gid)[0]
        if log_owner_name != "mysql" or log_owner_grp != "mysql":
            target_uid = pwd.getpwnam("mysql").pw_uid
            target_gid = grp.getgrnam("mysql").gr_gid
            os.chown(log_file, target_uid, target_gid)

        self.my_cnf_inspect()

        version = self._get_new_version()
        if version.startswith("mariadb") or version == "auto" \
                and self.cl_version >= 7:
            self._enable_mariadb()

        if version.startswith("mysql") \
                and self.cl_version >= 7:
            self._enable_mysql()

        if version.startswith("percona") \
                and self.cl_version >= 7:
            self._enable_percona()

        if not os.path.exists(self.VAR_LIB_MYSQL):
            os.makedirs(self.VAR_LIB_MYSQL)
            shutil.chown(self.VAR_LIB_MYSQL, user='mysql', group='mysql')

        self._mysqlservice("restart")

        print("Giving mysqld a few seconds to start up...")
        time.sleep(5)

        if is_package_installed("governor-mysql"):
            service("restart", "db_governor")
            print(bcolors.ok("DB-Governor installed/updated..."))

        self._after_install_new_packages()

        self._ld_fix()

        self._after_install()

        return True

    def install_rollback(self, beta):
        """
        Rollback installed version
        """
        if self.ALL_PACKAGES_OLD_NOT_DOWNLOADED:
            self.print_warning_about_not_complete_of_pkg_saving()
            print(bcolors.fail("Rollback disabled"))
            return False

        # to enable previously enabled mysql module
        self.cl8_enable_cached()

        # self._before_install_new_packages()
        self._mysqlservice("stop")

        installed_packages = self._load_current_packages(False)

        # remove new installed packages
        remove_packages(installed_packages)

        if os.path.exists("/etc/yum.repos.d/cl-mysql.repo.bak"):
            shutil.move("/etc/yum.repos.d/cl-mysql.repo.bak",
                        "/etc/yum.repos.d/cl-mysql.repo")

        # install deleted packages with triggers etc
        if self._custom_rpm_installer("", True) == "yes":
            install_packages("old", beta, self._custom_rpm_installer)
        else:
            install_packages("old", beta)

        # restore previous packages state
        # if os.path.exists("/etc/my.cnf.govprev"):
        #     shutil.move("/etc/my.cnf.govprev", "/etc/my.cnf")
        self.my_cnf_manager('restore')

        self._mysqlservice("restart")

        self._after_install_rollback()

        self.ROLLBACK = True

        return True

    def install_from_history(self, timestamp):
        """
        Install packages from history by timestamp value
        """
        try:
            timestamp = int(timestamp)
        except (TypeError, ValueError):
            print("Invalid parameters", file=sys.stderr)
            return False

        history_path = os.path.join(self.HISTORY_FOLDER, "old.%s" % timestamp)
        if not os.path.isdir(history_path):
            print("No packages for timestamp: %s" % timestamp, file=sys.stderr)
            return False

        self._mysqlservice("stop")

        # remove current installed packages
        installed_packages = self._load_current_packages(False)
        remove_packages(installed_packages)

        # install history packages
        install_packages(history_path, False, abs_path=True)

        # restore old config file
        # old_cnf = "%s/my.cnf" % history_path
        # if os.path.exists(old_cnf):
        #     shutil.copy(old_cnf, "/etc/my.cnf")
        self.my_cnf_manager('restore_old', history_path)

        self._mysqlservice("restart")

    def delete(self):
        """
        Delete governor packages
        """
        # first check config file
        check_file("/etc/my.cnf")

        # save current installed mysql version
        # self._save_previous_version()

        # get list of installed packages
        installed_packages = self._load_current_packages(download=False)

        installed_db_version = self._check_mysql_version().get('full')
        
        if not installed_db_version:
            print(bcolors.info("Current installed database couldn't be found. Exiting..."))
            exit(1)

        previous_db_version = self._get_previous_version()
        
        if previous_db_version == 'auto':
            previous_db_version = 'mysql80'

        print('installed_db_version ->', installed_db_version)
        print('previous_db_version ->', previous_db_version)

        if installed_db_version > previous_db_version:
            print("Not supported to downgrade database. Exiting...")
            exit(1)

        # remove repo file
        if os.path.exists("/etc/yum.repos.d/cl-mysql.repo"):
            shutil.move("/etc/yum.repos.d/cl-mysql.repo",
                        "/etc/yum.repos.d/cl-mysql.repo.bak")

        # remove cron file
        if os.path.exists("/etc/cron.d/dbgovernor-usermap-cron"):
            shutil.move("/etc/cron.d/dbgovernor-usermap-cron",
                        "/etc/cron.d/dbgovernor-usermap-cron.bak")

        # backup my.cnf file for restore if uninstall will be failed
        # if os.path.exists("/etc/my.cnf"):
        #     shutil.copy2("/etc/my.cnf", "/etc/my.cnf.govprev")
        self.my_cnf_manager('backup')

        # run trigger before governor uninstal
        self._before_delete()

        # run uninstall action
        self._delete(installed_packages)

        # run trigger after governor uninstall
        self._after_delete()

    def cl8_enable_cached(self):
        """
        Enable saved module stream, e.g. previously/initially enabled one (CL8 method only),
        or clean all mysql|mariadb|percona modules settings
        """
        if self.cl_version >= 8:
            if os.path.exists(self.CACHE_MODULE_FILE):
                with open(self.CACHE_MODULE_FILE) as module_file:
                    module = module_file.read()
                cl8_module_enable(module)
                print('Cached module: %s' % module)
            else:
                exec_command(
                    'dnf module disable -y mysql && dnf module disable -y mariadb && dnf module disable -y percona',
                    True, silent=True)

    def cl8_save_current(self):
        """
        Save currently enabled module stream (CL8 method only)
        """
        if self.cl_version >= 8:
            enabled_modules = exec_command('dnf module list --enabled --quiet | grep -iE "^mysql|mariadb|percona"',
                                           silent=True)
            try:
                current_module = ':'.join([l for l in enabled_modules[0].split(' ') if l][:2])
                print('Saving current enabled module: %s' % current_module)
                debug_log(exec_command('dnf module list --enabled', as_string=True))
                with open(self.CACHE_MODULE_FILE, 'w') as module_file:
                    module_file.write(current_module)
            except IndexError:
                pass

    def show_packages_history(self):
        """
        Show early downloaded packages
        """
        h = self.HISTORY_FOLDER

        for path in sorted(os.listdir(h)):
            full_path = os.path.join(h, path)
            if not os.path.isdir(full_path) or path.count(".") != 1:
                continue

            _, timestamp = path.split(".")
            try:
                timestamp = int(timestamp)
            except (ValueError, TypeError):
                continue

            date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
            print("DATE: %s, TS: %s" % (date, timestamp))
            for name in sorted(os.listdir(full_path)):
                print("    %s" % name)

    def clear_history_folder(self):
        """
        Remove all downloaded packages
        """
        if os.path.isdir(self.HISTORY_FOLDER):
            shutil.rmtree(self.HISTORY_FOLDER)
            os.mkdir(self.HISTORY_FOLDER, 0o755)
            os.chmod(self.HISTORY_FOLDER, 0o755)

    def cleanup(self):
        """
        Cleanup downloaded packages and remove backup repo file
        """
        # to enable previously enabled mysql module
        self.cl8_enable_cached()

        tmp_path = "%s/old" % RPM_TEMP_PATH
        if os.path.isdir(tmp_path):
            # first move previous downloaded packages to history folder
            history_path = os.path.join(self.HISTORY_FOLDER, "old.%s" %
                                        int(time.time()))
            shutil.move(tmp_path, history_path)
            # if os.path.exists("/etc/my.cnf.govprev"):
            #     shutil.move("/etc/my.cnf.govprev", "%s/my.cnf" % history_path)
            self.my_cnf_manager('backup_old', history_path)

        if os.path.exists(RPM_TEMP_PATH):
            shutil.rmtree(RPM_TEMP_PATH)

        if os.path.exists("/etc/yum.repos.d/cl-mysql.repo.bak"):
            os.unlink("/etc/yum.repos.d/cl-mysql.repo.bak")

        # if os.path.exists("/etc/my.cnf.govprev"):
        #     os.unlink("/etc/my.cnf.govprev")
        self.my_cnf_manager('cleanup')

        if os.path.exists("/etc/cron.d/dbgovernor-usermap-cron.bak"):
            os.unlink("/etc/cron.d/dbgovernor-usermap-cron.bak")

    def save_installed_version(self):
        """
        Save installed version number in file
        """
        self._save_previous_version()

    def update_user_map_file(self):
        """
        Update user mapping file.
        By default - empty
        """
        pass

    def set_bad_lve_container(self):
        """
        Function with some manipulations with lvectl and limits for container
        No more need in changing. Lets user decide by himself the value of the limits
        """
        return

    def install_mysql_beta_testing_hooks(self):
        """
        cPanel specific action
        """
        # self.set_fs_suid_dumpable()
        print("No need in fix")

    def fix_mysqld_service(self):
        """
        DA specific action
        """
        print("No need in fix")

    def set_mysql_version(self, version):
        """
        Set new mysql version for next install
        """
        # check available versions
        versions = ["auto"] + list(self.REPO_NAMES.keys())
        if version not in versions:
            print("Invalid mysql version.", file=sys.stderr)
            print("Available versions: %s" % ", ".join(versions), file=sys.stderr)
            sys.exit(1)

        write_file(self.NEW_VERSION_FILE, version)

    @staticmethod
    def set_fs_suid_dumpable():
        """
        Run this code in spec file
        """
        def check_io_perms():
            """
            Returns True if io is readable and False otherwise.
            Readable io means that fs.suid_dumpable could be 0, otherwise it should be 1 for governor's correct work
            """
            mode = os.stat('/proc/{0}/task/{0}/io'.format(os.getpid())).st_mode
            return stat.S_IMODE(mode) == 0o444
        suid_dumpable_state = 'fs.suid_dumpable={0:d}'.format(not check_io_perms())
        print("Setting FS suid_dumpable for governor to work correctly ({0})".format(suid_dumpable_state))
        exec_command_out("sysctl -w {0}".format(suid_dumpable_state))
        if os.path.exists("/etc/sysctl.conf"):
            if not grep("/etc/sysctl.conf", 'fs.suid_dumpable='):
                print("Adding suid_dumpable instruction to /etc/sysctl.conf for governor to work correctly")
                shutil.copy("/etc/sysctl.conf", "/etc/sysctl.conf.bak")
                add_line("/etc/sysctl.conf", suid_dumpable_state)
            else:
                print("Rewriting suid_dumpable instruction in /etc/sysctl.conf")
                with open("/etc/sysctl.conf", 'r+') as f:
                    rewrite_file(f, re.sub(r'fs.suid_dumpable=\d{1}', suid_dumpable_state, f.read()))
        else:
            print("Creating /etc/sysctl.conf for governor to work correctly")
            add_line("/etc/sysctl.conf", suid_dumpable_state)

    def _load_packages(self, beta):
        """
        Detect current mysql packages.
        Detect new mysql packages.
        Download rpm files of current and new mysql packages.
        """
        self._old_packages = self._load_current_packages()
        self._new_packages = self._load_new_packages(beta)

    @staticmethod
    def print_warning_about_not_complete_of_pkg_saving():
        """
        Display warning in case of failed download of old packages
        """
        print(bcolors.fail(
            """Restore of MySQL packages will not be completed because not \
all old packages were downloaded.\nCheck if all related repositories \
are enabled and try again\nIf something went wrong during \
or after installation process, execute \
/usr/share/lve/dbgovernor/mysqlgovernor --delete \
for native procedure restoring of MySQL packages"""))

    @staticmethod
    def print_warning_about_not_complete_of_newpkg_saving():
        """
        Display warning in case of failed download of new packages
        """
        print(bcolors.fail("Install of MySQL packages will not be completed " \
                           "because not all new packages have been downloaded"))

    def _load_current_packages(self, download=True, folder="old"):
        """
        here we download current installed packages
        @param `download` bool: download rpm files or
                                only return list of installed packages
        """
        if download:
            print(bcolors.info("Start download current installed packages"))
        else:
            print(bcolors.info("Get list of current installed packages"))

        PATTERNS = ["cl-mysql", "cl-mariadb", "cl-percona", "mysql", "mariadb",
                    "compat-mysql5", "Percona"]
        
        mysqld_path = exec_command("which mysqld", True, silent=True)
        pkg_name = False
        if mysqld_path:
            # print "No mysql presents on system"
            # return None

            # server package name
            # pkg_name = exec_command("""rpm -qf --qf "%%{name}
            # %%{version}\n" %s """ % mysqld_path, True, silent=True)
            check_if_mysql_installed = exec_command("""rpm -qf %s """ %
                                                    mysqld_path, True,
                                                    silent=True,
                                                    return_code=True)
            if check_if_mysql_installed == "no":
                print("No mysql packages installed, " \
                      "but mysqld file presents on system")
                pkg_name = None
            else:
                pkg_name = exec_command("""rpm -qf %s """ % mysqld_path, True,
                                        silent=True)

        # grep cl-MySQL packages in installed list
        # packages = exec_command("""rpm -qa --qf "%%{name}
        # %%{version}\n"|grep -iE "^(%s)" """ % "|".join(PATTERNS), silent=True)
        packages = exec_command("""rpm -qa|grep -iE "^(%s)" """ %
                                "|".join(PATTERNS), silent=True)
        # match pattern to exclude:
        # - mysql-community release package
        # - mysqld_exporter package
        # - MySQL-python package
        # from the list of packages to download
        pattern = r'MySQL-python|mysql(d_exporter|\d+-community-release)|mysql-common'
        packages = [x for x in packages if not re.match(pattern, x)]

        if not len(packages):
            print("No installed DB packages found")
            return False

        if pkg_name:
            found = False
            for pkg in packages:
                if pkg.startswith(pkg_name):
                    found = True
                    break

            if not found:
                packages.append(pkg_name)
                # print "Can`t find package with mysqld file"

        # self._old_packages = packages
        if download:
            # arch = ".x86_64" if os.uname()[-1] == "x86_64" else ""
            # download_pkgs = ["%s%s" % (x.split(" ")[0], arch)
            # for x in packages]
            IS_CL_MYSQL = False
            for package_item in packages:
                if "server" in package_item and package_item[:3] == "cl-":
                    IS_CL_MYSQL = True

            if IS_CL_MYSQL is True:
                if not download_packages(packages, folder, True):
                    self.ALL_PACKAGES_OLD_NOT_DOWNLOADED = True
            else:
                if not download_packages(packages, folder, True,
                                         self._custom_download_of_rpm):
                    print(bcolors.info("Trying to load custom packages from yum"))
                    if not download_packages(packages, folder, True):
                        self.ALL_PACKAGES_OLD_NOT_DOWNLOADED = True

        return packages

    def _get_result_mysql_version(self, sql_version=None):
        """
        Get MySQL version will be installed according to auto or mysql.type
        """
        sql_version = sql_version or self._get_new_version()

        if "auto" == sql_version:
            detected_version_on_system = self._detect_version_if_auto()
            if detected_version_on_system != "+":
                if detected_version_on_system == "":
                    print("Unknown SQL VERSION", file=sys.stderr)
                    sys.exit(1)
                else:
                    sql_version = detected_version_on_system
        return sql_version

    def get_repo_name(self, sql_version):
        return "cl-%s-common.repo" % self.REPO_NAMES.get(sql_version, None)

    def _load_new_packages(self, beta, sql_version=None, folder="new"):
        """
        detect and download packages for new installation
        """
        print(bcolors.info("Start download packages for new installation"))
        # based on sql_version get packages names list and repo name
        packages, requires = [], []
        module = None
        arch = ".x86_64" if os.uname()[-1] == "x86_64" else ""
        sql_version = self._get_result_mysql_version(sql_version)

        if "auto" == sql_version:
            repo = "mysql-common.repo"
            if self.cl_version == 7:
                packages = ["mariadb", "mariadb-server", "mariadb-devel", "mariadb-libs", "mariadb-bench"]
            else:
                packages = ["mysql", "mysql-server", "mysql-libs", "mysql-devel"]
                if self.cl_version < 8:
                    packages.append("mysql-bench")

            module = self.MODULE_STREAMS.get(sql_version, None)
            cl8_module_enable(module)
            # download and install only need arch packages
            packages = ["%s%s" % (x, arch) for x in packages]
            for line in exec_command("yum info %s" % packages[0]):
                if line.startswith("Version"):
                    sql_version = "%s%s" % (
                        packages[0].split('.')[0], "".join(line.split(":")[1].split(".")[:2]).strip())

        else:
            repo = self.get_repo_name(sql_version)
            module = self.MODULE_STREAMS.get(sql_version, None)

            if sql_version.startswith("mysql"):
                packages = ["cl-MySQL-meta", "cl-MySQL-meta-client",
                            "cl-MySQL-meta-devel"]
                requires = list(packages)

                # if sql_version in ["mysql56", "mysql57"]:
                # packages.append("libaio%s" % arch)

            elif sql_version.startswith("mariadb"):
                packages = ["cl-MariaDB-meta", "cl-MariaDB-meta-client",
                            "cl-MariaDB-meta-devel"]
                requires = packages[:3]
            elif sql_version.startswith("percona"):
                packages = ["cl-Percona-meta", "cl-Percona-meta-client",
                            "cl-Percona-meta-devel"]
                requires = packages[:3]
            else:
                print("Unknown SQL VERSION", file=sys.stderr)
                sys.exit(1)

        if sql_version == "mysql51":
            packages += ["mysqlclient18", "mysqlclient15"]
        elif sql_version.startswith('mysql'):
            # Install mysqlclient18 for all versions of mysql, even for 5.5 and 5.6
            # because from now it contains also libmariadb support needed
            # for some packages like net-snmp-agent-libs on CL8
            packages += ["mysqlclient16", "mysqlclient15", "mysqlclient18"]
            if sql_version in ["mysql57", "mysql80"]:
                packages += ["numactl-devel%s" % arch, "numactl%s" % arch]
        elif sql_version.startswith("mariadb"):
            packages += ["mysqlclient16", "mysqlclient15"]
            if sql_version in ["mariadb55", "mariadb100", "mariadb101", "mariadb102", "mariadb103"] \
                    and get_cl_num() == 8:
                # net-snmp-agent-libs on CL8 requires libmariadb.so.3() and libmariadb.so.3(libmysqlclient_18)
                # Old versions of MariaDB up to 10.1 do not contain libmariadb at all.
                # So we need to install mysqlclient18-compat for mariadb55, mariadb100 and mariadb101
                # Currently our meta-client pkgs of MariaDB 10.2 and 10.3 don't declare
                # that they provide libmariadb, though in fact their libs pkgs contain it.
                # So we need to install mysqlclient18-compat for mariadb102 and mariadb103 also.
                packages += ["mysqlclient18-compat"]
            elif sql_version == "mariadb106":
                packages += ["mysqlclient18"]
        elif sql_version.startswith("percona"):
            packages += ["mysqlclient18", "mysqlclient16", "mysqlclient15"]

        packages.append("libaio%s" % arch)

        repo_url = "http://repo.cloudlinux.com/other/cl%s/mysqlmeta/%s" % (
            self.cl_version, repo)

        try:
            content = urllib.request.urlopen(repo_url).read()
        except Exception as e:
            print("Can`t download repo file(%s): %s" % (repo_url, e), file=sys.stderr)
            #sys.exit(1)
            # Use default cl-mysql repo with mysqlclient only
            # expecting that meta packages are already available somewhere in predefined repos
            if os.path.exists("/etc/yum.repos.d/cl-mysql.repo"):
                shutil.copy2("/etc/yum.repos.d/cl-mysql.repo",
                             "/etc/yum.repos.d/cl-mysql.repo.bak")
            shutil.copy2("/usr/share/lve/dbgovernor/cl-mysql.repo.default",
                         "/etc/yum.repos.d/cl-mysql.repo")
            default_cl_mysql_repo = True
        else:
            if os.path.exists("/etc/yum.repos.d/cl-mysql.repo"):
                shutil.copy2("/etc/yum.repos.d/cl-mysql.repo",
                             "/etc/yum.repos.d/cl-mysql.repo.bak")
            write_file("/etc/yum.repos.d/cl-mysql.repo", content.decode())
            default_cl_mysql_repo = False

        # update repositories
        exec_command_out("yum clean all")
        cl8_module_enable(module)

        # Add requires to packages list
        if default_cl_mysql_repo:
            # We did not find specific repo for meta pkgs and installed default one instead,
            # So let's try to find meta pkgs in any repo
            for name in requires:
                packages += exec_command("repoquery --requires %s --quiet" % name)
        else:
            # We found specific repo for meta pkgs and installed it,
            # So let's try to find meta pkgs in it only
            for name in requires:
                req_packages = exec_command("repoquery --repoid cl-mysql-meta --requires %s --quiet" % name)
                if len(req_packages):
                    packages += req_packages
                else:
                    # in case of repos are already created but still empty - fallback to any repo case
                    packages += exec_command("repoquery --requires %s --quiet" % name)

        if not download_packages(packages, folder, beta):
            self.ALL_PACKAGES_NEW_NOT_DOWNLOADED = True

        return packages

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
            if not version_info:
                # for mysql 8.0
                version_info = re.findall(r'(?<=Ver\s)\S+', version_string[0])
                parts = version_info[0].split(' ')
            else:
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

    def check_need_for_mysql_upgrade(self):
        """
        Basic check for upgrading MySQL tables
        The True condition for mysql_upgrade is
            if mysql type has changed (mysql/mariadb)
            if version has changed
        :return: should upgrade or not (True or False)
        """
        current_version = self._check_mysql_version()
        if not self.prev_version or not current_version:
            print('Problem with version retrieving')
            return False
        return current_version['mysql_type'] != self.prev_version['mysql_type'] or current_version['short'] != self.prev_version['short']

    def run_mysql_upgrade(self):
        """
        Run mysql_upgrade and mysql_fix_privilege_tables scripts if it is needed
        """
        print('Check for the need of mysql_upgrade...')
        if self.check_need_for_mysql_upgrade():
            print('Tables should be upgraded!')
            if self.MYSQLPASSWORD:
                cmd_upgrade = "/usr/bin/mysql_upgrade --user='{user}' --password='{passwd}'".format(user=self.MYSQLUSER, passwd=self.MYSQLPASSWORD)
                cmd_fix = "/usr/bin/mysql_fix_privilege_tables --user='{user}' --password='{passwd}'".format(user=self.MYSQLUSER, passwd=self.MYSQLPASSWORD)
            else:
                cmd_upgrade = '/usr/bin/mysql_upgrade'
                cmd_fix = '/usr/bin/mysql_fix_privilege_tables'
            exec_command_out(cmd_upgrade)
            if os.path.exists('/usr/bin/mysql_fix_privilege_tables'):
                exec_command_out(cmd_fix)
        else:
            print('No need for upgrading tables')

    def _before_install_new_packages(self):
        """
        Specific actions before install new packages
        """

    def _after_install_new_packages(self):
        """
        Specific actions after install new packages
        """
        # patch governor config if needed
        self._set_mysql_access()
        # run mysql_upgrade if needed
        self.run_mysql_upgrade()
        print("The installation of MySQL for db_governor completed")

    def _after_install_rollback(self):
        """
        Panel-specified actions trigger for rollback bad installation
        """

    def _before_remove_old_packages(self):
        """
        Specific actions before removing old packages
        """
        # stop mysql server
        self._mysqlservice("stop")

    def _after_remove_old_packages(self):
        """
        Specific actions after removing old packages
        """

    def _before_delete(self):
        """
        Specific actions before delete
        """

    def _delete(self, installed_packages):
        """
        Remove installed packages and install new
        """
        print(bcolors.info("Removing mysql for db_governor start"))

        # download standard packages
        self._load_new_packages(False, "auto")

        # if not os.path.exists("/etc/my.cnf.bkp"):
        # shutil.copy2("/etc/my.cnf", "/etc/my.cnf.govprev")
        self.my_cnf_manager('backup')  # why without if exists?

        self._mysqlservice("stop")

        # remove governor package
        if IS_UBUNTU:
            exec_command_out('apt remove governor-mysql -y')
        else:
            exec_command_out("rpm -e governor-mysql")

        # delete installed packages
        remove_packages(installed_packages)

        # install auto packages
        if IS_UBUNTU:
            install_deb_packages('new')
        else:
            install_packages("new", False)
        self.cl8_save_current()

        print(bcolors.ok("Removing mysql for db_governor completed"))

    def _after_delete(self):
        """
        Specific actions after delete
        """
        force_update_cagefs()

    def _before_install(self):
        """
        Specific actions before governor installation
        """

    def _after_install(self):
        """
        Specific actions after governor installation
        """
        #force_update_cagefs()

    def _set_mysql_access(self):
        """
        Set mysql admin login and password and save it to governor config
        """
        self.get_mysql_user()
        if self.MYSQLUSER and self.MYSQLPASSWORD:
            print("Patch governor configuration file")
            check_file("/etc/container/mysql-governor.xml")
            patch_governor_config(self.MYSQLUSER, self.MYSQLPASSWORD)

            if is_package_installed('governor-mysql'):
                service("restart", "db_governor")
                print("DB-Governor restarted...")

    @staticmethod
    def _kill_mysql():
        """
        Kill mysqld processes.
        """
        if check_mysqld_is_alive():
            print("Stop hunging MySQL")
            exec_command_out("/usr/bin/killall -SIGTERM mysqld_safe")
            print("Waiting for mysqld_safe stop")
            time.sleep(10)
            exec_command_out("/usr/bin/killall -SIGTERM mysqld")
            print("Waiting for mysqld stop")
            time.sleep(10)

    def _enable_mariadb(self):
        """
        Enable mariaDB services
        """
        if self.cl_version >= 7:
            exec_command_out("systemctl enable mariadb.service")
            # MariaDB service file declare mysql and mysqld as its aliases
            # So they will be created as symlinks by "enable mariadb.service" command
            # Then those two commands lead to error like this:
            # Failed to execute operation: Too many levels of symbolic links
            #exec_command_out("systemctl enable mysql.service")
            #exec_command_out("systemctl enable mysqld.service")

    def _enable_mysql(self):
        """
        Enable MySQL services
        """
        if self.cl_version >= 7:
            exec_command_out("systemctl enable mysql.service")
            exec_command_out("systemctl enable mysqld.service")

    def _enable_percona(self):
        """
        Enable Percona service
        """
        if self.cl_version >= 7:
            exec_command_out("systemctl enable mysql.service")

    def _check_leave_pid(self):
        """
        Remove upgrade marker for mysql
        """
        print("Check for mysql pids and upgrade marker")
        if os.path.exists(f"{self.my_cnf_datadir}/RPM_UPGRADE_MARKER"):
            shutil.move(f"{self.my_cnf_datadir}/RPM_UPGRADE_MARKER",
                        f"{self.my_cnf_datadir}/RPM_UPGRADE_MARKER.old")

    @staticmethod
    def _ld_fix():
        """
        Fix shared library problems
        """
        if os.path.exists("/usr/lib64/mysql/libmygcc.a"):
            os.rename("/usr/lib64/mysql/libmygcc.a",
                      "/usr/lib64/mysql/libmygcc.a.bak")

        if os.path.exists("/usr/lib/mysql/libmygcc.a"):
            os.rename("/usr/lib/mysql/libmygcc.a",
                      "/usr/lib/mysql/libmygcc.a.bak")

        if os.path.exists("/sbin/ldconfig"):
            exec_command_out("/sbin/ldconfig")

    def _get_new_version(self):
        """
        Get new sql version for install
        """
        if os.path.exists(self.NEW_VERSION_FILE):
            return read_file(self.NEW_VERSION_FILE)
        return "auto"

    def _save_previous_version(self):
        """
        Save current installed mysql version to cache file.
        It will be previous version after new installation.
        """
        version = mysql_version()
        if version:
            write_file(self.CACHE_VERSION_FILE, version)

    def _get_previous_version(self):
        """
        Get current installed mysql version from cache file
        """
        if os.path.exists(self.CACHE_VERSION_FILE):
            return read_file(self.CACHE_VERSION_FILE)
        return 'auto'

    def _mysqlservice(self, action):
        """
        Stop mysql service
        """
        version = mysql_version()
        name = "mysql" if version in ["percona56", "mariadb55", "mariadb100"] \
            else "mysqld"
        if 6 == self.cl_version:
            if version in ["mysql51", "mysql55", "mysql56",
                           "mysql57", "mysql80", "mariadb101", "mariadb102",
                           "mariadb103", "mariadb104", "mariadb105", "mariadb106"]:
                name = "mysql"

        try:
            # service util now uses timeout
            service(action, name)
        except RuntimeError as e:
            print("Failed to {act} mysql service: {exc}. Please, check mysql service status and logs.".format(
                act=action, exc=e))
            sys.exit(3)

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

    def _script_subprocess(self, path, args=None):
        """
        Execute package script which locate in SOURCE directory
        """
        exec_command("%s %s" % (self._rel("scripts/%s" % path), args or ""))

    def _detect_version_if_auto(self):
        """
        What should we do if we get auto param in mysql.type
        """
        return "+"

    def _custom_download_of_rpm(self, package_name):
        """
        How we should to download installed MySQL package
        """
        return "no"

    def _custom_rpm_installer(self, package_name, indicator=False):
        """
        Specific rpm installer to use for given package name
        :param package_name: package to install
        :param indicator:
        :return:
        """
        return "no"

    def make_additional_panel_related_check(self):
        """
        Specific cPanel
        :return:
        """
        return

    def unsupported_db_version(self, force=False):
        """
        Skip an installation if not supported db version has been set:
        Update fom mysql80 to MariaDB 10.x version is not supported
        """
        current_version = self._check_mysql_version()
        if current_version.get('full') == 'mysql80':
            version = InstallManager._get_result_mysql_version(self)
            if version.startswith('mariadb10'):
                print(bcolors.fail(
                    """!!! WARNING !!!\nUpgrade from MySQL 8 to MariaDB 10.x \
isn't supported due to compatibility\nissues and will likely lead to a \
disaster / break your database server completely.\nIn order to save you, \
we've disabled this upgrade in DB Governor.\n!!! WARNING !!!\n\n\
A detailed explanation and workaround for CloudLinux can be found in this articles:\n\
MariaDB info about compatibility issue: https://mariadb.com/kb/en/upgrading-from-mysql-to-mariadb/\n\
Workaround for CloudLinux: https://cloudlinux.zendesk.com/hc/en-us/articles/360020599839"""))
                if not force:
                    sys.exit(1)

    def prepare_statement_for_ubuntu(self):
        """Specific actions before governor installation"""
