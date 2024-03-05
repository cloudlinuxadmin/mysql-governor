#!/opt/cloudlinux/venv/bin/python3
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
    check_mysqld_is_alive, fix_broken_governor_xml_config, get_status_info, get_supported_mysqls

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

def build_parser(supported_mysqls):
    """
    Build CLI parser
    """
    mysql_version_help = "select MySQL version for db-governor. Available mysql types: " + \
                          ', '.join(supported_mysqls)
    parser = argparse.ArgumentParser(prog="install-mysql", add_help=True,
                                     description="Use following syntax to "
                                                 "manage DBGOVERNOR install "
                                                 "utility:")
    parser.add_argument("--verbose", help="switch verbose level on",
                        dest="verbose", action="store_true", default=False)
    parser.add_argument("--mysql-version", help=mysql_version_help,
                        dest="mysql_version", required=False, choices=supported_mysqls)
    parser.add_argument("--mysql-version-list",
                        help="print list of the supported versions on mysql",
                        dest="mysql_version_list", action="store_true", default=False)
    parser.add_argument("-i", "--install", help="install MySQL for db-governor",
                            dest="install", action="store_true", default=False)
    parser.add_argument("--install-beta",
                        help="install MySQL beta for governor or update beta "
                             "if exists newer beta version",
                        dest="install_beta", action="store_true", default=False)
    parser.add_argument("--fix-cpanel-hooks",
                        help="fix adduser and deluser hooks for cPanel",
                        dest="fix_cpanel_hooks", action="store_true",
                        default=False)
    parser.add_argument("--update-cpanel-hooks",
                        help="update adduser and deluser hooks for cPanel",
                        dest="update_cpanel_hooks", action="store_true",
                        default=False)
    parser.add_argument("--fix-mysqld-service",
                        help="Restore mysqld.service for DirectAdmin",
                        dest="fix_mysqld_service", action="store_true",
                        default=False)
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
    parser.add_argument("--update-config-auth",
                        help="Update user login and password in config file",
                        dest="update_config", action="store_true",
                        default=False)
    parser.add_argument("--fix-config",
                        help="Fix unescaped xml and wrong limits in config file",
                        dest="fix_govervor_config", action="store_true",
                        default=False)
    return parser


def main(argv):
    """
    Run main actions
    """
    set_path_environ()
    sys.stdout = Logger(sys.stdout, LOG_FILE_NAME)
    sys.stderr = Logger(sys.stderr, LOG_FILE_NAME)
    shadow_tracing(False)
    time_now = datetime.datetime.now()
    sys.stdout.write_extended(
        "\n####################################################Install process begin %s#####################################################\n" % time_now.strftime(
            "%Y-%m-%d %H:%M"))

    panel = exec_command("cldetect --detect-cp-name", as_string=True)

    # Instead of IS_UBUNTU and get_cl_num()
    supported_mysqls = get_supported_mysqls(True, 8, panel)

    parser = build_parser(supported_mysqls)
    if not argv:
        parser.print_help()
        sys.exit(1)

    opts = parser.parse_args(argv)

    storage_holder = Storage()
    storage_holder.check_root_permissions()

    # create install manager instance for current cp
    manager = UbuntuInstallManager(panel)

    if opts.mysql_version_list:
        print(', '.join(supported_mysqls))
        sys.exit(0)

    if opts.debug_flag:
        set_debug(True)

    if opts.mysql_version:
        manager.set_mysql_version(opts.mysql_version)
        print(bcolors.ok("Now set MySQL to type '%s'" % opts.mysql_version))

    elif opts.install or opts.install_beta:
        manager.unsupported_db_version(opts.force)
        if not backup_warning(opts.yes or opts.wizard):
            sys.exit(0)
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
            elif opts.wizard or opts.yes or query_yes_no(
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
        manager.panel_manager.update_user_map_file()
    elif opts.fix_cpanel_hooks:
        manager.install_mysql_beta_testing_hooks()
    elif opts.update_cpanel_hooks:
        manager.update_mysql_hooks()
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


def backup_warning(yes):
    """
    :param yes: --yes flag or --wizard flag entered. Choose, if mode is interactive or no.
    In non-interactive mode print warning message and sleep 10 sec (for user to make a decision)
    In interactive mode print warning message and ask confirmation
    """
    print(bcolors.warning(
        "!!!Before making any changes to the database, make sure that you have a backup copy of users' data!!!"
    ))
    if yes:
        print(bcolors.fail(
            "!!!!!!!!!!!!!!!!!!!!!!!!!!Ctrl+C to cancel the installation!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        ))
    print(bcolors.ok(
        "Instruction: how to create a whole-database backup - "
        f"{bcolors.OKBLUE}http://docs.cloudlinux.com/index.html?backing_up_mysql.html"
    ))
    if yes:
        time.sleep(10)
        return True
    if not query_yes_no("Do you confirm that you've made a full backup of your MySQL databases?"):
        return False
    return True


if "__main__" == __name__:
    main(sys.argv[1:])
