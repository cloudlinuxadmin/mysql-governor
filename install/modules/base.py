# coding:utf-8
"""
This module contains base class for managing governor on all supported
control panels
"""
import math
import os
import shutil
import sys
import time
import urllib2
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
    check_mysqld_is_alive, makedir_recursive, patch_governor_config
from ConfigParser import RawConfigParser


class InstallManager(object):
    """
    Base class with standard methods for any CP
    """
    # installation path
    SOURCE = "/usr/share/lve/dbgovernor/"
    # file with new version for install
    NEW_VERSION_FILE = "/usr/share/lve/dbgovernor/mysql.type"
    # file with cached installed version before install
    CACHE_VERSION_FILE = "/usr/share/lve/dbgovernor/mysql.type.installed"
    HISTORY_FOLDER = "/usr/share/lve/dbgovernor/history"
    REPO_NAMES = {
        "mysql50": "mysql-5.0",
        "mysql51": "mysql-5.1",
        "mysql55": "mysql-5.5",
        "mysql56": "mysql-5.6",
        "mysql57": "mysql-5.7",
        "mariadb55": "mariadb-5.5",
        "mariadb100": "mariadb-10.0",
        "mariadb101": "mariadb-10.1",
        "mariadb102": "mariadb-10.2",
        "percona56": "percona-5.6"
    }
    ALL_PACKAGES_NEW_NOT_DOWNLOADED = False
    ALL_PACKAGES_OLD_NOT_DOWNLOADED = False
    DISABLED = False
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

    @staticmethod
    def my_cnf_manager(action, old_path=None):
        """
        Allows to manage known manipulations with /etc/my.cnf file
        :param action: action to perform
        :param old_path: path to my.cnf if needed
        """
        # fix for packages without /etc/my.cnf file
        if action == 'touch':
            touch("/etc/my.cnf")
            return

        actions = {
            'backup': lambda x: shutil.copy2(x, "/etc/my.cnf.prev"),
            'restore': lambda x: shutil.move(x, "/etc/my.cnf"),
            'restore_old': lambda x: shutil.copy(x, "/etc/my.cnf"),
            'restore_rpmsave': lambda x: shutil.copy2(x, "/etc/my.cnf"),
            'cleanup': lambda x: os.unlink(x),
            'backup_old': '',
        }

        if action not in actions.keys():
            raise RuntimeError('Cannot manage /etc/my.cnf: '
                               'unknown action %s' % action)

        if action == 'backup':
            working_path = "/etc/my.cnf"
        elif action == 'restore_old':
            working_path = "%s/my.cnf" % old_path
        else:
            working_path = "/etc/my.cnf.prev"

        if os.path.exists(working_path):
            if action == 'backup_old':
                shutil.move(working_path, "%s/my.cnf" % old_path)
            else:
                actions.get(action)(working_path)

    def my_cnf_inspect(self):
        """
        Fix nonexistent paths to log-error and pid-file
        """
        self.my_cnf_manager('backup')
        track = {
            'files': ('log-error', ),
            'paths': ('pid-file', )
        }
        default_log = '/var/lib/mysql/mysqld.error.log'
        default_pid = '/var/lib/mysql/mysqld.pid'

        conf = RawConfigParser(allow_no_value=True)
        conf.read('/etc/my.cnf.prev')
        # try to find non-existent paths, defined in /etc/my.cnf
        for s in conf.sections():
            for opt, val in conf.items(s):
                if opt in track['files']:
                    # inspect whole path
                    if not os.path.exists(val):
                        print 'NO LOG for {opt} --> {v}'.format(opt=opt, v=val)
                        conf.set(s, opt, default_log)
                elif opt in track['paths']:
                    # inspect dir path
                    if not os.path.exists(os.path.dirname(val)):
                        print 'NO PATH for {opt} --> {v}'.format(opt=opt, v=val)
                        conf.set(s, opt, default_pid)

        with open('/etc/my.cnf', 'wb') as configfile:
            conf.write(configfile)

    def remove_current_packages(self):
        """
        Delete current installed packages
        """
        # stop mysql service
        self._mysqlservice("stop")
        # disable service for CL7 to eliminate broken symlinks after removing
        if self.cl_version == 7:
            self._mysqlservice("disable")

        # remove current mysql packages
        remove_packages(self._old_packages)

    def install(self, beta, no_confirm):
        """
        Install stable or beta packages
        @param `beta` bool: install beta or production
        @param `path` str: path to packages for install
        """
        if not self.cl_version:
            print "Unknown system type. Installation aborted"
            sys.exit(2)

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

        if not confirm_packages_installation("new", no_confirm):
            self.DISABLED = True
            return False

        # if os.path.exists("/etc/my.cnf"):
        #     shutil.copy2("/etc/my.cnf", "/etc/my.cnf.prev")
        self.my_cnf_manager('backup')

        create_mysqld_link("mysqld", "mysql")
        create_mysqld_link("mysql", "mysqld")

        # first remove installed mysql packages
        self.remove_current_packages()

        correct_remove_notowned_mysql_service_names_cl7()
        correct_remove_notowned_mysql_service_names_not_symlynks_cl7()

        # restore my.cnf, because removing of packages
        # renames /etc/my.cnf to /etc/my.cnf.rpmsave
        # if os.path.exists("/etc/my.cnf.prev"):
        #     shutil.copy2("/etc/my.cnf.prev", "/etc/my.cnf")
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
                and self.cl_version == 7:
            self._enable_mariadb()

        if version.startswith("mysql") \
                and self.cl_version == 7:
            self._enable_mysql()

        if version.startswith("percona") \
                and self.cl_version == 7:
            self._enable_percona()

        self._mysqlservice("restart")

        print "Giving mysqld a few seconds to start up..."
        time.sleep(5)

        if is_package_installed("governor-mysql"):
            service("restart", "db_governor")
            print "DB-Governor installed/updated..."

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
            print "Rollback disabled"
            return

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
        # if os.path.exists("/etc/my.cnf.prev"):
        #     shutil.move("/etc/my.cnf.prev", "/etc/my.cnf")
        self.my_cnf_manager('restore')

        self._mysqlservice("restart")

        self._after_install_rollback()

    def install_from_history(self, timestamp):
        """
        Install packages from history by timestamp value
        """
        try:
            timestamp = int(timestamp)
        except (TypeError, ValueError):
            print >> sys.stderr, "Invalid parameters"
            return False

        history_path = os.path.join(self.HISTORY_FOLDER, "old.%s" % timestamp)
        if not os.path.isdir(history_path):
            print >> sys.stderr, "No packages for timestamp: %s" % timestamp
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
        self._save_previous_version()

        # get list of installed packages
        installed_packages = self._load_current_packages()

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
        #     shutil.copy2("/etc/my.cnf", "/etc/my.cnf.prev")
        self.my_cnf_manager('backup')

        # run trigger before governor uninstal
        self._before_delete()

        # run uninstall action
        self._delete(installed_packages)

        # run trigger after governor uninstall
        self._after_delete()

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
            print "DATE: %s, TS: %s" % (date, timestamp)
            for name in sorted(os.listdir(full_path)):
                print "    %s" % name

    def clear_history_folder(self):
        """
        Remove all downloaded packages
        """
        if os.path.isdir(self.HISTORY_FOLDER):
            shutil.rmtree(self.HISTORY_FOLDER)
            os.mkdir(self.HISTORY_FOLDER, 0755)
            os.chmod(self.HISTORY_FOLDER, 0755)

    def cleanup(self):
        """
        Cleanup downloaded packages and remove backup repo file
        """
        tmp_path = "%s/old" % RPM_TEMP_PATH
        if os.path.isdir(tmp_path):
            # first move previous downloaded packages to history folder
            history_path = os.path.join(self.HISTORY_FOLDER, "old.%s" %
                                        int(time.time()))
            shutil.move(tmp_path, history_path)
            # if os.path.exists("/etc/my.cnf.prev"):
            #     shutil.move("/etc/my.cnf.prev", "%s/my.cnf" % history_path)
            self.my_cnf_manager('backup_old', history_path)

        if os.path.exists(RPM_TEMP_PATH):
            shutil.rmtree(RPM_TEMP_PATH)

        if os.path.exists("/etc/yum.repos.d/cl-mysql.repo.bak"):
            os.unlink("/etc/yum.repos.d/cl-mysql.repo.bak")

        # if os.path.exists("/etc/my.cnf.prev"):
        #     os.unlink("/etc/my.cnf.prev")
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
        print "No need in fix"

    def fix_mysqld_service(self):
        """
        DA specific action
        """
        print "No need in fix"

    def set_mysql_version(self, version):
        """
        Set new mysql version for next install
        """
        # check available versions
        versions = ["auto"] + self.REPO_NAMES.keys()
        if version not in versions:
            print >> sys.stderr, "Invalid mysql version."
            print >> sys.stderr, "Available versions: %s" % ", ".join(versions)
            sys.exit(2)

        write_file(self.NEW_VERSION_FILE, version)

    @staticmethod
    def set_fs_suid_dumpable():
        """
        Run this code in spec file
        """
        print "Set FS suid_dumpable for governor to work correctly"
        exec_command_out("sysctl -w fs.suid_dumpable=1")
        if os.path.exists("/etc/sysctl.conf"):
            if not grep("/etc/sysctl.conf", "fs.suid_dumpable=1"):
                print "Add to /etc/sysctl.conf suid_dumpable instruction " \
                      "for governor to work correctly"
                shutil.copy("/etc/sysctl.conf", "/etc/sysctl.conf.bak")
                add_line("/etc/sysctl.conf", "fs.suid_dumpable=1")
            else:
                print "Everything is present in /etc/sysctl.conf " \
                      "for governor to work correctly"
        else:
            print "Create /etc/sysctl.conf for governor to work correctly"
            add_line("/etc/sysctl.conf", "fs.suid_dumpable=1")

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
        print """Restore of MySQL packages will not be completed because
        not all old packages was downloaded. If something went wrong during
        or after installation process,
        execute /usr/share/lve/dbgovernor/mysqlgovernor --delete
        for native procedure restoring of MySQL packages"""

    @staticmethod
    def print_warning_about_not_complete_of_newpkg_saving():
        """
        Display warning in case of failed download of new packages
        """
        print "Install of MySQL packages will not be completed because " \
              "not all new packages have been downloaded"

    def _load_current_packages(self, download=True, folder="old"):
        """
        here we download current installed packages
        @param `download` bool: download rpm files or
                                only return list of installed packages
        """
        print "Start download current installed packages"
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
                print "No mysql packages installed, " \
                      "but mysqld file presents on system"
                pkg_name = None
            else:
                pkg_name = exec_command("""rpm -qf %s """ % mysqld_path, True,
                                        silent=True)

        # grep cl-MySQL packages in installed list
        # packages = exec_command("""rpm -qa --qf "%%{name}
        # %%{version}\n"|grep -iE "^(%s)" """ % "|".join(PATTERNS), silent=True)
        packages = exec_command("""rpm -qa|grep -iE "^(%s)" """ %
                                "|".join(PATTERNS), silent=True)

        if not len(packages):
            print "No installed DB packages found"
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

            if IS_CL_MYSQL == True:
                if not download_packages(packages, folder, True):
                    self.ALL_PACKAGES_OLD_NOT_DOWNLOADED = True
            else:
                if not download_packages(packages, folder, True,
                                         self._custom_download_of_rpm):
                    print "Trying to load custom packages from yum"
                    if not download_packages(packages, folder, True):
                        self.ALL_PACKAGES_OLD_NOT_DOWNLOADED = True

        return packages
        # return [x.replace(" ", "-") for x in packages]

    def _get_result_mysql_version(self, sql_version=None):
        """
        Get MySQL version will be installed according to auto or mysql.type
        """
        sql_version = sql_version or self._get_new_version()

        if "auto" == sql_version:
            detected_version_on_system = self._detect_version_if_auto()
            if detected_version_on_system != "+":
                if detected_version_on_system == "":
                    print >> sys.stderr, "Unknown SQL VERSION"
                    sys.exit(2)
                else:
                    sql_version = detected_version_on_system
        return sql_version

    def _load_new_packages(self, beta, sql_version=None, folder="new"):
        """
        detect and download packages for new installation
        """
        print "Start download packages for new installation"
        # based on sql_version get packages names list and repo name
        packages, requires = [], []
        arch = ".x86_64" if os.uname()[-1] == "x86_64" else ""
        sql_version = self._get_result_mysql_version(sql_version)

        if "auto" == sql_version:
            repo = "mysql-common.repo"
            if 7 != self.cl_version:
                packages = ["mysql", "mysql-server", "mysql-libs",
                            "mysql-devel", "mysql-bench"]
            else:
                packages = ["mariadb", "mariadb-server", "mariadb-libs",
                            "mariadb-devel", "mariadb-bench"]

            # download and install only need arch packages
            packages = ["%s%s" % (x, arch) for x in packages]
            for line in exec_command("yum info %s" % packages[0]):
                if line.startswith("Version"):
                    sql_version = "%s%s" % (
                        packages[0].split('.')[0], "".join(line.split(":")[1].split(".")[:2]).strip())

        else:
            repo = "cl-%s-common.repo" % self.REPO_NAMES.get(sql_version, None)

            if sql_version in ["mysql50", "mysql51", "mysql55", "mysql56",
                               "mysql57"]:
                packages = ["cl-MySQL-meta", "cl-MySQL-meta-client",
                            "cl-MySQL-meta-devel"]
                requires = list(packages)

                # if sql_version in ["mysql56", "mysql57"]:
                # packages.append("libaio%s" % arch)

            elif sql_version in ["mariadb55", "mariadb100", "mariadb101",
                                 "mariadb102"]:
                packages = ["cl-MariaDB-meta", "cl-MariaDB-meta-client",
                            "cl-MariaDB-meta-devel"]
                requires = packages[:3]
            elif sql_version in ["percona56"]:
                packages = ["cl-Percona-meta", "cl-Percona-meta-client",
                            "cl-Percona-meta-devel"]
                requires = packages[:3]
            else:
                print >> sys.stderr, "Unknown SQL VERSION"
                sys.exit(2)

        if sql_version == "mysql50":
            packages += ["mysqlclient18", "mysqlclient16"]
        elif sql_version == "mysql51":
            packages += ["mysqlclient18", "mysqlclient15"]
        elif sql_version in ["mysql55", "mysql56", "mysql57"]:
            packages += ["mysqlclient16", "mysqlclient15"]
            if sql_version in ["mysql57"]:
                packages += ["numactl-devel%s" % arch, "numactl%s" % arch, "mysqlclient18"]
        elif sql_version.startswith("mariadb"):
            packages += ["mysqlclient16", "mysqlclient15"]
            if sql_version == 'mariadb102':
                packages += ["mysqlclient18-compat"]
        elif sql_version.startswith("percona"):
            packages += ["mysqlclient16", "mysqlclient15"]

        packages.append("libaio%s" % arch)

        repo_url = "http://repo.cloudlinux.com/other/cl%s/mysqlmeta/%s" % (
            self.cl_version, repo)
        try:
            content = urllib2.urlopen(repo_url).read()
        except Exception, e:
            print >> sys.stderr, "Can`t download repo file: %s" % e
            sys.exit(2)
        else:
            if os.path.exists("/etc/yum.repos.d/cl-mysql.repo"):
                shutil.copy2("/etc/yum.repos.d/cl-mysql.repo",
                             "/etc/yum.repos.d/cl-mysql.repo.bak")
            write_file("/etc/yum.repos.d/cl-mysql.repo", content)

        # update repositories
        exec_command_out("yum clean all")

        # Add requires to packages list
        for name in requires:
            # query only for non-installed packages
            packages += exec_command("repoquery --requires %s" % name)
            # query for installed package
            # exec_command("rpm -q --requires cl-MySQL-meta")

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
            print 'Problem with version retrieving'
            return False
        return current_version['mysql_type'] != self.prev_version['mysql_type'] or current_version['short'] != self.prev_version['short']

    def run_mysql_upgrade(self):
        """
        Run mysql_upgrade and mysql_fix_privilege_tables scripts if it is needed
        """
        print 'Check for the need of mysql_upgrade...'
        if self.check_need_for_mysql_upgrade():
            print 'Tables should be upgraded!'
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
            print 'No need for upgrading tables'

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
        print "The installation of MySQL for db_governor completed"

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
        print "Removing mysql for db_governor start"

        # download standard packages
        self._load_new_packages(False, "auto")

        # if not os.path.exists("/etc/my.cnf.bkp"):
        # shutil.copy2("/etc/my.cnf", "/etc/my.cnf.prev")
        self.my_cnf_manager('backup')  # why without if exists?

        self._mysqlservice("stop")

        # remove governor package
        exec_command_out("rpm -e governor-mysql")

        # delete installed packages
        remove_packages(installed_packages)

        # install auto packages
        install_packages("new", False)

        print "Removing mysql for db_governor completed"

    def _after_delete(self):
        """
        Specific actions after delete
        """

    def _before_install(self):
        """
        Specific actions before governor installation
        """

    def _after_install(self):
        """
        Specific actions after governor installation
        """

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

    @staticmethod
    def _kill_mysql():
        """
        Kill mysqld processes.
        """
        if check_mysqld_is_alive():
            print "Stop hunging MySQL"
            exec_command_out("/usr/bin/killall -SIGTERM mysqld_safe")
            print "Waiting for mysqld_safe stop"
            time.sleep(10)
            exec_command_out("/usr/bin/killall -SIGTERM mysqld")
            print "Waiting for mysqld stop"
            time.sleep(10)

    def _enable_mariadb(self):
        """
        Enable mariaDB services
        """
        if 7 == self.cl_version:
            exec_command_out("systemctl enable mariadb.service")
            exec_command_out("systemctl enable mysql.service")
            exec_command_out("systemctl enable mysqld.service")

    def _enable_mysql(self):
        """
        Enable MySQL services
        """
        if 7 == self.cl_version:
            exec_command_out("systemctl enable mysql.service")
            exec_command_out("systemctl enable mysqld.service")

    def _enable_percona(self):
        """
        Enable Percona service
        """
        if 7 == self.cl_version:
            exec_command_out("systemctl enable mysql.service")

    @staticmethod
    def _check_leave_pid():
        """
        Remove upgrade marker for mysql
        """
        print "Check for mysql pids and upgrade marker"
        if os.path.exists("/var/lib/mysql/RPM_UPGRADE_MARKER"):
            shutil.move("/var/lib/mysql/RPM_UPGRADE_MARKER",
                        "/var/lib/mysql/RPM_UPGRADE_MARKER.old")

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
            read_file(self.CACHE_VERSION_FILE)

        return None

    def _mysqlservice(self, action):
        """
        Stop mysql service
        """
        version = mysql_version()
        name = "mysql" if version in ["percona56", "mariadb55", "mariadb100"] \
            else "mysqld"
        if 6 == self.cl_version:
            if version in ["mysql50", "mysql51", "mysql55", "mysql56",
                           "mysql57", "mariadb101", "mariadb102"]:
                name = "mysql"

        service(action, name)

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
