#!/opt/alt/python27/bin/python2.7
# coding:utf-8
"""
Main mysql-governor installation script
"""
import argparse
import sys
import time
import datetime
import os
import re

from clcommon import cpapi

from modules import InstallManager
from utilities import bcolors, set_debug, shadow_tracing, set_path_environ, \
    fix_broken_governor_xml_config, patch_init_d_scripts, set_fs_suid_dumpable, \
    sysconfig_patch, restore_governor_xml_config

LOG_FILE_NAME = "/usr/share/lve/dbgovernor2/governor_install.log"


class Logger(object):
    """
    Logger class
    """
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")
        os.chmod(filename, 0o600)
        self.escape_pattern = re.compile(r"\033(\[[0-9;]*m|\(B)")

    def write(self, message):
        """
        Write message to logfile and stdout
        :param message:
        """
        self.terminal.write(message)
        self.log.write(self.escape_pattern.sub('', message))

    def write_extended(self, message):
        """
        Write message to logfile only
        :param message:
        """
        self.log.write(self.escape_pattern.sub('', message))


def build_parser():
    """
    Build CLI parser
    """
    parser = argparse.ArgumentParser(prog="mysqlgovernor", add_help=True,
                                     description="Use following syntax to "
                                                 "manage DBGOVERNOR install "
                                                 "utility:")
    parser.add_argument("--verbose", help="switch verbose level on",
                        dest="verbose", action="store_true", default=False)
    parser.add_argument("--mysql-version",
                        help="select MySQL version for db-governor. "
                             "Available mysql types: mysql55, mysql56, mysql57,"
                             " mariadb55, mariadb100, mariadb101, mariadb102",
                        dest="mysql_version", required=False,
                        choices=['mysql55', 'mysql56', 'mysql57', 'mariadb55',
                                 'mariadb100', 'mariadb101', 'mariadb102'])
    parser.add_argument("-i", "--install", help="install governor MySQL plugin",
                        dest="install", action="store_true", default=False)
    parser.add_argument("-d", "--delete", help="delete governor MySQL plugin",
                        dest="delete", action="store_true", default=False)
    parser.add_argument("--install-beta",
                        help="install MySQL beta for governor or update beta "
                             "if exists newer beta version",
                        dest="install_beta", action="store_true", default=False)
    parser.add_argument("-c", "--clean-mysql",
                        help="clean MySQL packages list "
                             "(after governor installation)",
                        dest="clean_mysql", action="store_true", default=False)
    parser.add_argument("-m", "--clean-mysql-delete",
                        help="clean cl-MySQL packages list "
                             "(after governor deletion)",
                        dest="clean_mysql_delete", action="store_true",
                        default=False)
    parser.add_argument("-t", "--dbupdate", help="update UserMap file",
                        dest="dbupdate", action="store_true", default=False)
    parser.add_argument("-y", "--yes",
                        help="Perform migration without confirm",
                        dest="assume_yes", action="store_true", default=False)
    parser.add_argument("--fix-cpanel-hooks",
                        help="fix adduser and deluser hooks for cPanel",
                        dest="fix_cpanel_hooks", action="store_true",
                        default=False)
    parser.add_argument("--force",
                        help="Automatically perform migration to official "
                             "MySQL/MariaDB versions if CloudLinux packages found",
                        dest="force", action="store_true", default=False)
    parser.add_argument("--fresh",
                        help="Automatic installation of requested official "
                             "MySQL/MariaDB for fresh systems with no DB",
                        dest="fresh", action="store_true", default=False)
    parser.add_argument("-u", "--upgrade",
                        help="Option is deprecated. Use `yum update` instead",
                        dest="upgrade", action="store_true", default=False)
    parser.add_argument("--update-mysql-beta",
                        help="Option is deprecated. Use --install-beta instead",
                        dest="update_mysql_beta", action="store_true",
                        default=False)
    parser.add_argument("--fs-suid", help="Helper utility", dest="fs_suid",
                        action="store_true", default=False)
    parser.add_argument("--list-saved-files",
                        help="Show list of saved MySQL old files in storage",
                        dest="store_list", action="store_true", default=False)
    parser.add_argument("--save-file-to-storage", help="Save file to storage",
                        dest="store_save", required=False)
    parser.add_argument("--restore-file-from-storage",
                        help="Restore file from storage",
                        dest="store_restore", required=False)
    parser.add_argument("--save-files-from-list",
                        help="Save file to storage according to files list "
                             "/usr/share/lve/dbgovernor2/list_problem_files.txt",
                        dest="store_list_files", action="store_true",
                        default=False)
    parser.add_argument("--restore-all-files",
                        help="Restore all files from storage",
                        dest="restore_list_all", action="store_true",
                        default=False)
    parser.add_argument("--clean-storage", help="Clean up storage",
                        dest="store_clean", action="store_true", default=False)
    parser.add_argument("--correct-cl7-service-name",
                        help="Remove /etc/init.d/mysql(d) "
                             "if exists for CloudLinux 7",
                        dest="cl7_correct", action="store_true", default=False)
    parser.add_argument("--output-commands",
                        help="Echo all commands executed by "
                             "governor's install script",
                        dest="debug_flag", action="store_true", default=False)
    parser.add_argument("--show-previous-packages",
                        help="Show list of early downloaded packages",
                        dest="show_previous_packages", action="store_true",
                        default=False)
    parser.add_argument("--install-from-history",
                        help="Restore previous downloaded packages",
                        dest="install_from_history", required=False)
    parser.add_argument("--clear-history",
                        help="Delete previous downloaded packages",
                        dest="clear_history", action="store_true",
                        default=False)
    parser.add_argument("--correct-cloud-version",
                        help="Fix error in cloudlinux.versions file",
                        dest="clver_correct", action="store_true",
                        default=False)
    parser.add_argument("--fix-config",
                        help="Fix unescaped xml and wrong limits in config file",
                        dest="fix_govervor_config", action="store_true",
                        default=False)
    parser.add_argument("--restore-config",
                        help="Restore mysql-governor.xml if necessary",
                        dest="restore_governor_config",  action="store_true",
                        default=False)
    parser.add_argument("--update-mysql-plugin",
                        help="Update governor-mysql plugin",
                        dest="update_plugin", action="store_true",
                        default=False)
    parser.add_argument("--initd-patch",
                        help="Patch init.d mysql scripts",
                        dest="initd_patch", action="store_true",
                        default=False)
    parser.add_argument("--sysconfig",
                        help="Patch or clean sysconfig",
                        dest="sysconfig_action", choices=['update', 'clean'])
    return parser


def main(argv):
    """
    Run main actions
    """
    set_path_environ()
    sys.stdout = Logger(LOG_FILE_NAME)
    sys.stderr = Logger(LOG_FILE_NAME)
    shadow_tracing(True)
    time_now = datetime.datetime.now()
    sys.stdout.write_extended(
        "\n####################################################Install process begin %s#####################################################\n" % time_now.strftime(
            "%Y-%m-%d %H:%M"))

    parser = build_parser()
    if not argv:
        parser.print_help()
        sys.exit(2)

    opts = parser.parse_args(argv)

    if opts.debug_flag:
        set_debug(True)

    if opts.fs_suid:
        set_fs_suid_dumpable()
    elif opts.fix_govervor_config:
        fix_broken_governor_xml_config()
    elif opts.restore_governor_config:
        restore_governor_xml_config()
    elif opts.initd_patch:
        patch_init_d_scripts()
    elif opts.sysconfig_action:
        sysconfig_patch(opts.sysconfig_action)
    elif opts.fix_cpanel_hooks:
        print "Option is deprecated."
    elif opts.install_from_history:
        print "Option is deprecated."
    elif opts.show_previous_packages:
        print "Option is deprecated."
    elif opts.clear_history:
        print "Option is deprecated."
    elif opts.clean_mysql:
        print "Option is deprecated."
    elif opts.clean_mysql_delete:
        print "Option is deprecated."
    elif opts.upgrade:
        print "Option is deprecated. Use `yum update` instead."
    elif opts.update_mysql_beta:
        print "Option is deprecated. Use --install-beta instead."
    elif opts.store_list:
        print "Option is deprecated."
    elif opts.clver_correct:
        print "Option is deprecated."
    elif opts.store_save:
        print "Option is deprecated."
    elif opts.store_restore:
        print "Option is deprecated."
    elif opts.store_list_files:
        print "Option is deprecated."
    elif opts.restore_list_all:
        print "Option is deprecated."
    elif opts.store_clean:
        print "Option is deprecated."
    elif opts.cl7_correct:
        print "Option is deprecated."
    elif opts.install_beta:
        print "Option is deprecated."
    else:
        # create install manager instance for current cp
        manager = InstallManager.factory(cpapi.CP_NAME)

        if opts.install:
            manager.install(opts.force, opts.assume_yes)
        elif opts.update_plugin:
            manager.update_plugin()
        elif opts.delete:
            manager.delete()
        elif opts.mysql_version:
            manager.migrate(opts.mysql_version, opts.fresh, opts.assume_yes)
        elif opts.dbupdate:
            manager.update_user_map_file()
        else:
            parser.print_help()
            sys.exit(2)

    sys.exit(0)


def warn_message():
    """
    Print warning message and sleep 10 sec (for user to make a decision)
    """
    print bcolors.warning("!!!Before making any changing with database make sure that you have reserve copy of users data!!!")
    print bcolors.fail("!!!!!!!!!!!!!!!!!!!!!!!!!!Ctrl+C for cancellation of installation!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print bcolors.ok("Instruction: how to create whole database backup - ") + bcolors.info("http://docs.cloudlinux.com/index.html?backing_up_mysql.html")
    time.sleep(10)


if "__main__" == __name__:
    main(sys.argv[1:])
