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
import hashlib
import urllib2
from distutils.version import LooseVersion

sys.path.append("../")

from utilities import get_cl_num, exec_command, exec_command_out, service, \
    check_file, patch_governor_config, remove_packages, bcolors


class InstallManager(object):
    """
    Base class with standard methods for any CP
    """
    # installation path
    SOURCE = "/usr/share/lve/dbgovernor/"
    PLUGIN_3 = '/usr/share/lve/dbgovernor/plugins/libgovernorplugin3.so'
    PLUGIN_4 = '/usr/share/lve/dbgovernor/plugins/libgovernorplugin4.so'
    PLUGIN_DEST = '%(plugin_path)sgovernor.so'
    PLUGIN_MD5 = '/usr/share/lve/dbgovernor/plugin.md5'
    PLUGIN_PATH = '/usr/share/lve/dbgovernor/plugin.dir'
    MYSQLUSER = ''
    MYSQLPASSWORD = ''

    supported = {
        'mysql': '5.5.14',
        'mariadb': '5.5.37'
    }

    ALL_NEW_PKGS_LOADED = False
    RPM_PATH = '/usr/share/lve/dbgovernor/rpms'

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

    def __init__(self, cp_name):
        self.cl_version = get_cl_num()
        self.cp_name = cp_name
        self.get_mysql_user()
        self.mysql_version = self._check_mysql_version()
        try:
            self.installed_plugin = self.find_plugin()
        except Exception:
            print bcolors.warning('Cannot resolve plugin directory. MySQL/MariaDB is not running?')

    def install(self):
        """
        Governor plugin installation
        """
        if not self.cl_version:
            print bcolors.fail("Unknown system type. Installation aborted")
            sys.exit(2)

        # patch governor config
        self._set_mysql_access()

        self._governorservice('stop')
        # try uninstalling old governor plugin
        try:
            print 'Try to uninstall old governor plugin...'
            self.mysql_command('uninstall plugin governor')
        except RuntimeError as e:
            print e
        self._mysqlservice('restart')

        if not self.mysql_version:
            print bcolors.warning('No installed MySQL/MariaDB found')
            print bcolors.fail('Cannot install plugin')
            print bcolors.ok('You may use mysqlgovernor.py to install officially supported MySQL/MariaDB: for example')
            print bcolors.info('\t/usr/share/lve/dbgovernor/mysqlgovernor.py --mysql-version mysql56')
            print bcolors.info('\t/usr/share/lve/dbgovernor/mysqlgovernor.py --mysql-version mariadb100')
        else:
            print bcolors.ok('{} {} is installed here'.format(self.mysql_version['mysql_type'],
                                                              self.mysql_version['extended']))
            if LooseVersion(self.mysql_version['extended']) < LooseVersion(self.supported[self.mysql_version['mysql_type']]):
                print bcolors.fail("{t} {v} is unsupported by governor plugin.")
                print bcolors.info("Support starts from {s}".format(t=self.mysql_version['mysql_type'],
                                                                    v=self.mysql_version['extended'],
                                                                    s=self.supported[self.mysql_version['mysql_type']]))
                sys.exit(2)

            if self.mysql_version['patched']:
                print bcolors.warning('This is PATCHED {}!'.format(self.mysql_version['mysql_type']))
                print bcolors.fail('Abort plugin installation')
                print bcolors.ok('Please, install officially supported MySQL/MariaDB.\nYou may use mysqlgovernor.py for this: for example')
                print bcolors.info('\t/usr/share/lve/dbgovernor/mysqlgovernor.py --mysql-version {}'.format(self.mysql_version['full']))
            else:
                print bcolors.ok('Installing plugin...')
                # copy corresponding plugin to mysql plugins' location
                governor_plugin = self.PLUGIN_4 if self.plugin4() else self.PLUGIN_3
                if os.path.exists(governor_plugin):
                    # install plugin
                    print 'Selected file %s' % governor_plugin
                    shutil.copy(governor_plugin, self.installed_plugin)
                    self.mysql_command('install plugin governor soname "governor.so"')
                    self.plugin_md5('write')
                    print bcolors.ok('Governor plugin installed successfully.')
        self._governorservice('start')
        return True

    def delete(self):
        """
        Delete governor
        """
        self._governorservice('stop')
        # try uninstalling old governor plugin
        try:
            print 'Try to uninstall old governor plugin...'
            self.mysql_command('uninstall plugin governor')
        except RuntimeError as e:
            print e

        self._mysqlservice('stop')
        try:
            os.unlink(self.installed_plugin)
            print 'Plugin deleted'
            os.unlink(self.PLUGIN_MD5)
            print 'Plugin.md5 deleted'
            os.unlink(self.PLUGIN_PATH)
            print 'Plugin.dir deleted'
        except (IOError, OSError) as e:
            print e
        for script in ('/etc/init.d/mysql', '/etc/init.d/mysqld', '/etc/init.d/mariadb'):
            try:
                shutil.move(script + '.bak', script)
                print '{} restored'.format(script)
            except (IOError, OSError):
                continue
        self._mysqlservice('start')

    def update_plugin(self):
        """
        Determine if plugin should be updated with the help of md5 sum
        :return: True if should False otherwise
        """
        new_plugin = self.PLUGIN_4 if self.plugin4() else self.PLUGIN_3
        plugin_md5_sum = self.plugin_md5('read')
        if plugin_md5_sum:
            new_plugin_md5 = hashlib.md5(open(new_plugin, 'rb').read()).hexdigest()
            if new_plugin_md5 != plugin_md5_sum:
                print 'Updating governor plugin...'
                shutil.copy(new_plugin, self.installed_plugin)
                self.plugin_md5('write')
                self._mysqlservice('restart')
                print 'Governor plugin updated successfully'
            else:
                print 'No need in updating governor plugin'
        else:
            print 'Nothing to update. Governor plugin is not installed?'

    def plugin_md5(self, action):
        """
        Read/write md5_sum to file for installed plugin
        :param action: read or write
        :return: calculated md5 sum
        """
        # read file if file exists
        if action == 'read' and os.path.exists(self.PLUGIN_MD5):
            print 'Read plugin.md5'
            with open(self.PLUGIN_MD5, 'rb') as md5_file:
                md5 = md5_file.read()
        # write file if plugin is installed
        elif action == 'write' and os.path.exists(self.installed_plugin):
            print 'Write new plugin.md5'
            md5 = hashlib.md5(open(self.installed_plugin, 'rb').read()).hexdigest()
            with open(self.PLUGIN_MD5, 'wb') as md5_file:
                md5_file.write(md5)
        else:
            return None
        print '\t-->{}'.format(md5)
        return md5.strip()

    def find_plugin(self):
        """
        Try to resolve path to installed governor plugin:
        read file with path to plugin directory or ask mysql about plugin_dir
        :return: path to governor plugin
        """
        if os.path.exists(self.PLUGIN_PATH):
            with open(self.PLUGIN_PATH, 'rb') as plugin_dir_file:
                plugin_path = plugin_dir_file.read()
        else:
            _, plugin_path = self.mysql_command('select @@plugin_dir')
            with open(self.PLUGIN_PATH, 'wb') as plugin_dir_file:
                plugin_dir_file.write(plugin_path)
        return self.PLUGIN_DEST % {'plugin_path': plugin_path}

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

    def _check_mysql_version(self):
        """
        Retrieve MySQL version from mysql --version command
        :return: dictionary with version of form {
                short: two numbers of version (e.g. 5.5)
                extended: all numbers of version (e.g. 5.5.52)
                mysql_type: type flag (mysql or mariadb)
                full: mysql_type + short version (e.g. mariadb55)
                patched: cll-lve or not (e.g. True/False)
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
            result = exec_command('/usr/bin/strings /usr/sbin/mysqld | grep my_pthread_lvemutex_unlock | wc -l')
            version.update({'patched': result[0] == '1'})
        except Exception:
            return {}
        return version

    def plugin4(self):
        """
        Should we set plugin of 4th version or not
        :return: True if plugin 4 is needed False otherwise
        """
        return self.mysql_version['mysql_type'] == 'mysql' and LooseVersion(self.mysql_version['extended']) >= LooseVersion('5.7.9')

    def mysql_command(self, command):
        """
        Execute mysql query via command line
        :param command: query to execute
        :return: result of query execution
        """
        if self.MYSQLUSER and self.MYSQLPASSWORD:
            result = exec_command("""mysql -u'{user}' -p'{passwd}' -e '{cmd};'""".format(user=self.MYSQLUSER,
                                                                                passwd=self.MYSQLPASSWORD,
                                                                                cmd=command))
        else:
            result = exec_command("""mysql -e '{cmd};'""".format(cmd=command))
        return result

    def _set_mysql_access(self):
        """
        Set mysql admin login and password and save it to governor config
        """
        # self.get_mysql_user()
        if self.MYSQLUSER and self.MYSQLPASSWORD:
            print "Patch governor configuration file"
            check_file("/etc/container/mysql-governor.xml")
            patch_governor_config(self.MYSQLUSER, self.MYSQLPASSWORD)

            if exec_command("rpm -qa governor-mysql", True):
                service("restart", "db_governor")
                print "DB-Governor restarted..."

    def migrate(self, new_version):
        """
        Perform migration to given new_version
        """
        if self.is_migration_possible(new_version):
            self.install_official(new_version)
        else:
            print bcolors.fail('Unable to perform migration.')

    def is_migration_possible(self, new_version):
        """
        Check if migration to given version is possible
        :param new_version: version to migrate to
        :return:
        """
        migration_table = {
            'mysql55': ('mysql56', 'mariadb55'),
            'mysql56': ('mysql57', 'mariadb100'),
            'mysql57': (),
            'mariadb55': ('mysql56', 'mariadb100'),
            'mariadb100': ('mysql56', 'mariadb101'),
            'mariadb101': ('mysql57', 'mariadb102'),
            'mariadb102': ()
        }
        if not self.mysql_version or self.mysql_version['patched']:
            return True
        elif new_version == self.mysql_version['full']:
            print bcolors.ok('No need to migrate, you have {} already installed'.format(new_version))
            return False
        else:
            if new_version in migration_table[self.mysql_version['full']]:
                print bcolors.ok('Starting migration to {}'.format(new_version))
            else:
                print bcolors.fail('You selected either downgrade, or upgrade over a generation, which are not allowed both.')
            return new_version in migration_table[self.mysql_version['full']]

    def install_official(self, version):
        """
        Install official MySQL/MariaDB
        Download required packages, then delete old, then install downloaded
        :param version: version to install
        """
        # preparation
        self._before_install_mysql()
        pkgs = self.prepare(version)
        # download packages
        self.ALL_NEW_PKGS_LOADED = self.download_packages(pkgs)
        # uninstall old and install new
        if self.ALL_NEW_PKGS_LOADED:
            if self.mysql_version:
                self.uninstall_mysql()
            self.install_packages()
            self._after_install_mysql()
            print bcolors.ok('Successfully migrated to {}!'.format(version))
        else:
            print bcolors.fail('FAILED to download packages for new MySQL/MariDB installation!')
            print bcolors.fail('Unable to perform migration.')

    def install_packages(self):
        """
        Install downloaded packages
        :return:
        """
        print 'Installing new packages:\n\t--> {pkgs}'.format(pkgs='\n\t--> '.join(os.listdir(self.RPM_PATH)))
        exec_command('yum install -y *', cwd=self.RPM_PATH)

    def download_packages(self, names):
        """
        Download packages before installation
        Two steps:
            normal download or update with yum
            download of broken packages with yumdownloader if normal failed
        :param names: packages names (iterable)
        :return: True of False based on procedure success
        """
        print bcolors.info('Downloading official packages')
        if not os.path.exists(self.RPM_PATH):
            os.makedirs(self.RPM_PATH, 0755)
        else:
            shutil.rmtree(self.RPM_PATH)

        download_proc = self.download_updates if self.is_update(names) else self.common_download

        if not download_proc(names):
            print bcolors.warning('Failed to download packages with yum. Trying yumdownloader instead...')
            return self.download_broken(names)
        else:
            return True

    def common_download(self, names):
        """
        Download packages with yum --downloadonly
        :param names: packages names (iterable)
        :return: True of False based on command success
        """
        res = exec_command(
            "yum install -y --downloadonly --disableexcludes=all --downloaddir={dst} {pkgs}".format(
                dst=self.RPM_PATH,
                pkgs=' '.join(names)), return_code=True)
        return res == 'yes'

    def download_broken(self, names):
        """
        Download conflicting packages with yumdownloader
        :param names: packages names (iterable)
        :return: True of False based on command success
        """
        # utilize LC_ALL locale variable setting in order to grep control start string
        old_var = os.getenv('LC_ALL')
        os.putenv('LC_ALL', 'en_US.UTF-8')
        # find out problem packages names
        res = exec_command(
            "yum install -y --skip-broken --downloadonly --disableexcludes=all --downloaddir={dst} {pkgs}".format(
                dst=self.RPM_PATH,
                pkgs=' '.join(names)), silent=True)
        try:
            start = res.index('Packages skipped because of dependency problems:') + 1
            conflicting_pkgs = [l.split('from')[0].strip() for l in res[start:]]
        except Exception:
            return False

        # download packages
        r = exec_command(
            "yumdownloader --disableexcludes=all --destdir={dst} {pkgs}".format(
                dst=self.RPM_PATH,
                pkgs=' '.join(conflicting_pkgs)), return_code=True)
        # restore LC_ALL variable
        os.putenv('LC_ALL', old_var if old_var else '')
        return r == 'yes'

    def download_updates(self, names):
        """
        Download packages in update mode
        :param names: packages names (iterable) -- for compatibility purposes
        :return: True of False based on command success
        """
        repo = names[0].split('-')[0].lower()
        print 'Download updates from repo {}'.format(repo)
        res = exec_command(
            "yum update -y --downloadonly --disableexcludes=all --downloaddir={dst} --disablerepo='*' --enablerepo='{name}'".format(
                dst=self.RPM_PATH, name=repo), return_code=True)
        return res == 'yes'

    def is_update(self, pkgs_names):
        """
        Check if requested packages are an update for installed ones
        This is specific for MariaDB packages
        :param pkgs_names: packages names (iterable)
        :return: True or False
        """
        name = pkgs_names[0].split('-')[0].lower()
        if not self.mysql_version or self.mysql_version['patched']:
            return False
        elif name == 'mysql':
            return False
        else:
            return self.mysql_version['mysql_type'] == name

    def prepare(self, version):
        """
        Prepare required official repository and resolve packages list
        :param version: version to install
        :return: packages list
        """
        exec_command('yum clean all')
        if version.startswith('mysql'):
            pkgs = self.prepare_official_mysql(version)
        elif version.startswith('mariadb'):
            pkgs = self.prepare_official_mariadb(version)
        else:
            print bcolors.fail('Unknown database requested!\nOnly official MySQL/MariDB supported')
            sys.exit(2)
        return pkgs

    def prepare_official_mysql(self, version):
        """
        Prepare official MySQL repository and packages
        :param version: mysql version
        """
        pkg = ('mysql-community-server', )
        if not exec_command('rpm -qa | grep mysql57-community', silent=True):
            self.download_and_install_mysql_repo()

        # select and install MySQL
        print 'Selected version %s' % version
        exec_command('yum-config-manager --disable mysql*-community')
        exec_command('yum-config-manager --enable {version}-community'.format(version=version))
        return pkg

    def prepare_official_mariadb(self, version):
        """
        Prepare official MariaDB repository and packages
        :param version: mariadb version
        """
        pkgs = ('MariaDB-server', 'MariaDB-client', 'MariaDB-shared')
        self.install_mariadb_repo(version)
        return pkgs

    def download_and_install_mysql_repo(self):
        """
        Download mysql57-community-release repository and install it locally
        """
        # download repo file
        url = 'https://dev.mysql.com/get/mysql57-community-release-el{v}-11.noarch.rpm'.format(v=self.cl_version)
        repo_file = os.path.join(self.SOURCE, 'mysql-community-release.rpm')
        repo_md5 = {
            6: 'afe0706ac68155bf91ade1c55058fd78',
            7: 'c070b754ce2de9f714ab4db4736c7e05'
        }
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]

        print 'Downloading %s' % url
        rpm = opener.open(url).read()
        with open(repo_file, 'wb') as f:
            f.write(rpm)

        if hashlib.md5(open(repo_file, 'rb').read()).hexdigest() != repo_md5[self.cl_version]:
            print 'Failed to download MySQL repository file. File is corrupted!'
            sys.exit(2)

        # install repo
        exec_command_out('yum localinstall -y {}'.format(repo_file))

    def install_mariadb_repo(self, version):
        """
        Create MariaDB repository file
        """
        repo_data = """[mariadb]
name = MariaDB
baseurl = http://yum.mariadb.org/{maria_ver}/centos{cl_ver}-{arch}
gpgkey=https://yum.mariadb.org/RPM-GPG-KEY-MariaDB
gpgcheck=1
"""
        num = version.split('mariadb')[-1]
        mariadb_version = '{base}.{suffix}'.format(base=num[:-1],
                                                   suffix=num[-1])
        arch = 'amd64' if os.uname()[-1] == 'x86_64' else 'x86'
        with open('/etc/yum.repos.d/MariaDB.repo', 'wb') as repo_file:
            repo_file.write(
                repo_data.format(maria_ver=mariadb_version,
                                 cl_ver=self.cl_version, arch=arch))

    def uninstall_mysql(self):
        """
        Remove existing MySQL/MariaDB (for migration purposes)
        """
        print bcolors.warning('Going to uninstall existing MySQL/MariaDB --%s--' % self.mysql_version['full'])
        installed_pkgs = self._get_installed_packages()
        print 'These packages are going to be removed:\n\t--> {}'.format('\n\t--> '.join(installed_pkgs))
        remove_packages(installed_pkgs)

    @staticmethod
    def _get_installed_packages():
        """
        Find out the list of currently installed DB packages
        (this could be neither our packages, nor official ones)
            - check mysqld path
            - find out which package owns mysqld server (e.g. *-server pkg)
            - resolve packages list on the basis of the server name beginning
        """
        known_patterns = ["cl-mysql", "cl-mariadb", "cl-percona", "mysql",
                          "mariadb", "compat-mysql5", "Percona"]
        packages = list()
        # check who owns mysqld
        mysqld_path = exec_command("which mysqld", True, silent=True)
        if mysqld_path:
            check_if_mysql_installed = exec_command('rpm -qf {}'.format(mysqld_path),
                                                    True, silent=True,
                                                    return_code=True)
            if check_if_mysql_installed == "no":
                print bcolors.warning("No mysql packages installed, but mysqld file presents on system")
            else:
                # find out server package name
                pkg_name = exec_command('rpm -qf {}'.format(mysqld_path), True,
                                        silent=True)
                # resolve other packages names
                packages = exec_command("""rpm -qa|grep -iE "^{}" """.format(pkg_name.split('-server')[0]),
                                        silent=True)
                # try to resolve out meta packages
                if pkg_name.startswith('cl-'):
                    packages.extend(exec_command("""rpm -qa|grep -iE "^cl-"|grep "meta" """,
                                                 silent=True))
        else:
            # check known packages patterns if no mysqld found
            packages = exec_command("""rpm -qa|grep -iE "^({})" """.format("|".join(known_patterns)),
                                    silent=True)
        return packages

    def run_mysql_upgrade(self):
        """
        Run mysql_upgrade and mysql_fix_privilege_tables scripts
        """
        if self.MYSQLPASSWORD:
            cmd_upgrade = "/usr/bin/mysql_upgrade --user='{user}' --password='{passwd}'".format(user=self.MYSQLUSER, passwd=self.MYSQLPASSWORD)
            cmd_fix = "/usr/bin/mysql_fix_privilege_tables --user='{user}' --password='{passwd}'".format(user=self.MYSQLUSER, passwd=self.MYSQLPASSWORD)
        else:
            cmd_upgrade = '/usr/bin/mysql_upgrade'
            cmd_fix = '/usr/bin/mysql_fix_privilege_tables'

        exec_command(cmd_upgrade)
        if os.path.exists('/usr/bin/mysql_fix_privilege_tables'):
            exec_command_out(cmd_fix)

    def _before_install_mysql(self):
        """
        Actions, performed prior to MySQL/MariaDB installation process
        """
        if self.mysql_version:
            self._mysqlservice('stop')

    def _after_install_mysql(self):
        """
        Actions, performed after MySQL/MariaDB installation process
        """
        self._mysqlservice('start')
        if self.cp_name == 'Unknown':
            self.run_mysql_upgrade()

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
