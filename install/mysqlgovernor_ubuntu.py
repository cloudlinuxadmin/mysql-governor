#!/opt/alt/python37/bin/python3
# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
"""
Main mysql-governor installation script
"""
import argparse
import sys
import time
import datetime
import os
from modules import UbuntuInstallManager, Storage
from utilities import exec_command, bcolors, query_yes_no, \
    correct_mysqld_service_for_cl7, set_debug, shadow_tracing, set_path_environ, \
    check_mysqld_is_alive, fix_broken_governor_xml_config, get_status_info

LOG_FILE_NAME = "/usr/share/lve/dbgovernor/governor_install.log"


class Logger:
    """
    Logger class
    """
    def __init__(self, stream, filename="Default.log"):
        self.terminal = stream
        self.log = open(filename, "a")
        os.chmod(filename, 0o600)

    def write(self, message):
        """
        Write message to logfile and stdout
        :param message:
        """
        self.terminal.write(message)
        self.log.write(message)

    def write_extended(self, message):
        """
        Write message to logfile only
        :param message:
        """
        self.log.write(message)

    def flush(self):
        self.terminal.flush()


def build_parser():
    """
    Build CLI parser
    """
    parser = argparse.ArgumentParser(prog="install-mysql", add_help=True,
                                     description="Use following syntax to "
                                                 "manage DBGOVERNOR install "
                                                 "utility:")
    parser.add_argument("--verbose", help="switch verbose level on",
                        dest="verbose", action="store_true", default=False)
    parser.add_argument("--mysql-version",
                        help="select MySQL version for db-governor. "
                             "Available mysql types: auto, mysql80, mariadb103",
                        dest="mysql_version", required=False,
                        choices=['auto', 'mysql80', 'mariadb103'])
    parser.add_argument("-i", "--install", help="install MySQL for db-governor",
                        dest="install", action="store_true", default=False)
    parser.add_argument("--install-beta",
                        help="install MySQL beta for governor or update beta "
                             "if exists newer beta version",
                        dest="install_beta", action="store_true", default=False)
    parser.add_argument("--force",
                        help="Force prohibited update, for example, upgrade from MySQL 8.0 to MariaDB 10.x",
                        dest="force", action="store_true", default=False)
    parser.add_argument("--yes", help="Install without confirm", dest="yes",
                        action="store_true", default=False)
    parser.add_argument("--output-commands",
                        help="Echo all commands executed by "
                             "governor's install script",
                        dest="debug_flag", action="store_true", default=False)
    parser.add_argument("--wizard", help="Wizard mode on", dest="wizard", action="store_true", default=False)
    parser.add_argument("--status", help="Check status info", dest="check_status", action="store_true", default=False)
    parser.add_argument("-d", "--delete", help="delete MySQL for db-governor",
                        dest="delete", action="store_true", default=False)
    parser.add_argument("-t", "--dbupdate", help="update UserMap file",
                        dest="dbupdate", action="store_true", default=False)
    return parser


def main(argv):
    """
    Run main actions
    """
    set_path_environ()
    sys.stdout = Logger(sys.stdout, LOG_FILE_NAME)
    sys.stderr = Logger(sys.stderr, LOG_FILE_NAME)
    shadow_tracing(True)
    time_now = datetime.datetime.now()
    sys.stdout.write_extended(
        "\n####################################################Install process begin %s#####################################################\n" % time_now.strftime(
            "%Y-%m-%d %H:%M"))

    parser = build_parser()
    if not argv:
        parser.print_help()
        sys.exit(1)

    opts = parser.parse_args(argv)

    storage_holder = Storage()
    storage_holder.check_root_permissions()

    # create install manager instance for current cp
    manager = UbuntuInstallManager()

    if opts.debug_flag:
        set_debug(True)
    if opts.mysql_version:
        manager.set_mysql_version(opts.mysql_version)
        print(bcolors.ok("Now set MySQL to type '%s'" % opts.mysql_version))

    elif opts.install or opts.install_beta:
        manager.unsupported_db_version(opts.force)
        warn_message()
        manager.cleanup()

        # remove current packages and install new packages
        if manager.install(opts.install_beta, opts.yes, opts.wizard):
            print("Give mysql service time to start before service checking(15 sec)")
            time.sleep(15)
        else:
            sys.exit(0) if manager.DISABLED else sys.exit(1)

        # check mysqld service status
        if not manager.ALL_PACKAGES_NEW_NOT_DOWNLOADED and not manager.DISABLED:
            if check_mysqld_is_alive():
                manager.save_installed_version()
                manager.cl8_save_current()
                print(bcolors.ok("Installation of mysql for db_governor completed"))

            # if sql server failed to start ask user to restore old packages
            elif opts.wizard or query_yes_no(
                    "Installation failed. Restore previous version?"):
                print(bcolors.fail(
                    "Installation of mysql for db_governor failed. Restore previous mysql version..."))
                if not manager.install_rollback(opts.install_beta):
                    sys.exit(1)

        manager.cleanup()
        if manager.ROLLBACK:
            print(bcolors.ok("Rollback finished"))
            sys.exit(3)

    elif opts.delete:
        manager.delete()
        print("Deletion is complete")

        manager.cleanup()
    elif opts.dbupdate:
        manager.update_user_map_file()
    elif opts.fix_cpanel_hooks:
        manager.install_mysql_beta_testing_hooks()
    elif opts.install_from_history:
        manager.install_from_history(opts.install_from_history)
    elif opts.show_previous_packages:
        manager.show_packages_history()
    elif opts.clear_history:
        manager.clear_history_folder()
    elif opts.clean_mysql:
        print("Option is deprecated.")
    elif opts.clean_mysql_delete:
        print("Option is deprecated.")
    elif opts.upgrade:
        print("Option is deprecated. Use `yum update` instead.")
    elif opts.update_mysql_beta:
        print("Option is deprecated. Use --install-beta instead.")
    elif opts.fs_suid:
        manager.set_fs_suid_dumpable()
    elif opts.store_list:
        storage_holder.list_files_from_storage(False)
    elif opts.clver_correct:
        manager.make_additional_panel_related_check()
    elif opts.store_save:
        storage_holder.save_file_to_storage(opts.store_save)
    elif opts.store_restore:
        storage_holder.restore_file_from_storage(opts.store_restore)
    elif opts.store_list_files:
        storage_holder.apply_files_from_list(
            "/usr/share/lve/dbgovernor/list_problem_files.txt")
    elif opts.restore_list_all:
        storage_holder.list_files_from_storage(True)
    elif opts.store_clean:
        storage_holder.empty_storage()
    elif opts.cl7_correct:
        correct_mysqld_service_for_cl7("mysql")
        correct_mysqld_service_for_cl7("mysqld")
    elif opts.fix_govervor_config:
        fix_broken_governor_xml_config()
    elif opts.fix_mysqld_service:
        manager.fix_mysqld_service()
    elif opts.update_config:
        manager._set_mysql_access()
    elif opts.check_status:
        sys.exit(0) if get_status_info() else sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


def detect_percona(force, install_manager_instance):
    """
    Detect unsupported Percona packages
    :param force:
    :param install_manager_instance:
    """
    if force:
        return None

    packages = exec_command("""rpm -qa|grep -iE "^percona-" """, silent=True)
    if len(packages):
        print("Percona packages deteced:" + ",".join(packages))
        print("You are running Percona, which is not supported by " \
              "MySQL Governor. If you want to run MySQL governor, " \
              "we would have to uninstall Percona, and substitute it " \
              "for MariaDB or MySQL. Run installator next commands for install:")
        print(install_manager_instance.rel("mysqlgovernor.py") + \
              " --mysql-version=mysql56 (or mysql50, mysql51, mysql55, " \
              "mysql57, mariadb55, mariadb100, mariadb101)")
        print(install_manager_instance.rel("mysqlgovernor.py") + \
              " --install --force")
        sys.exit(1)


def warn_message():
    """
    Print warning message and sleep 10 sec (for user to make a decision)
    """
    print(bcolors.warning("!!!Before making any changing with database make sure that you have reserve copy of users data!!!"))
    print(bcolors.fail("!!!!!!!!!!!!!!!!!!!!!!!!!!Ctrl+C for cancellation of installation!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"))
    print(bcolors.ok("Instruction: how to create whole database backup - " + bcolors.OKBLUE + "http://docs.cloudlinux.com/index.html?backing_up_mysql.html"))
    time.sleep(10)


if "__main__" == __name__:
    main(sys.argv[1:])
