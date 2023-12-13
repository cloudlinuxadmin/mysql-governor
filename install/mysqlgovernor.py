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
import datetime
import os
import sys
import time

from modules import InstallManager, Storage
from utilities import (bcolors, check_mysqld_is_alive,
                       correct_mysqld_service_for_cl7, exec_command,
                       fix_broken_governor_xml_config, get_cl_num,
                       get_status_info, query_yes_no, set_debug,
                       set_path_environ, get_supported_mysqls)

# from utilities import shadow_tracing

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
        """
        Flush the attached terminal.
        """
        self.terminal.flush()


def build_parser(supported_mysqls):
    """
    Build CLI parser
    """
    mysql_version_help = "select MySQL version for db-governor. Available MySQL types: " + \
                           ', '.join(supported_mysqls)
    parser = argparse.ArgumentParser(prog="install-mysql", add_help=True,
                                     description="Use the following syntax to "
                                                 "manage the DBGOVERNOR install "
                                                 "utility:")
    parser.add_argument("--verbose", help="switch verbose level on",
                        dest="verbose", action="store_true", default=False)
    parser.add_argument("--mysql-version", help=mysql_version_help,
                        dest="mysql_version", required=False, choices=supported_mysqls)
    parser.add_argument("--mysql-version-list",
                        help="print list of the supported MySQL versions",
                        dest="mysql_version_list", action="store_true", default=False)
    parser.add_argument("-i", "--install", help="install MySQL for db-governor",
                        dest="install", action="store_true", default=False)
    parser.add_argument("-d", "--delete", help="delete MySQL for db-governor",
                        dest="delete", action="store_true", default=False)
    parser.add_argument("--install-beta",
                        help="install MySQL beta for governor or update beta "
                             "if a newer beta version exists",
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
    parser.add_argument("--fix-cpanel-hooks",
                        help="fix adduser and deluser hooks for cPanel",
                        dest="fix_cpanel_hooks", action="store_true",
                        default=False)
    parser.add_argument("--update-cpanel-hooks",
                        help="update adduser and deluser hooks for cPanel",
                        dest="update_cpanel_hooks", action="store_true",
                        default=False)
    parser.add_argument("--force",
                        help="Force a prohibited update, for example, upgrade from MySQL 8.0 to MariaDB 10.x",
                        dest="force", action="store_true", default=False)
    parser.add_argument("-u", "--upgrade",
                        help="Option is deprecated. Use `yum update` instead",
                        dest="upgrade", action="store_true", default=False)
    parser.add_argument("--update-mysql-beta",
                        help="Option is deprecated. Use --install-beta instead",
                        dest="update_mysql_beta", action="store_true",
                        default=False)
    parser.add_argument("--fs-suid", help="Helper utility", dest="fs_suid",
                        action="store_true", default=False)
    parser.add_argument("--yes", help="Install without confirmation", dest="yes",
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
                        help="Save file to storage according to the files list "
                             "/usr/share/lve/dbgovernor/list_problem_files.txt",
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
                             "if it exists for CloudLinux 7",
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
                        help="Fix unescaped XML and wrong limits in the config file",
                        dest="fix_govervor_config", action="store_true",
                        default=False)
    parser.add_argument("--fix-mysqld-service",
                        help="Restore mysqld.service for DirectAdmin",
                        dest="fix_mysqld_service", action="store_true",
                        default=False)
    parser.add_argument("--update-config-auth",
                        help="Update user login and password in the config file",
                        dest="update_config", action="store_true",
                        default=False)
    parser.add_argument("--wizard", help="Wizard mode on", dest="wizard", action="store_true", default=False)
    parser.add_argument("--status", help="Check status info", dest="check_status", action="store_true", default=False)
    return parser


def main(argv):
    """
    Run main actions
    """
    set_path_environ()
    sys.stdout = Logger(sys.stdout, LOG_FILE_NAME)
    sys.stderr = Logger(sys.stderr, LOG_FILE_NAME)
    time_now = datetime.datetime.now()
    time_formatted = time_now.strftime("%Y-%m-%d %H:%M")
    sys.stdout.write_extended(
        "\n####################################################"
        f"Installation process starting at {time_formatted}"
        "#####################################################\n"
    )

    # get panel name
    panel = exec_command("cldetect --detect-cp-name", as_string=True)
    supported_mysqls = get_supported_mysqls(False, get_cl_num(), panel)

    parser = build_parser(supported_mysqls)
    if not argv:
        parser.print_help()
        sys.exit(1)

    opts = parser.parse_args(argv)

    storage_holder = Storage()
    storage_holder.check_root_permissions()

    # create install manager instance for current cp
    manager = InstallManager.factory(panel)

    if opts.mysql_version_list:
        print(', '.join(supported_mysqls))
        sys.exit(0)

    if opts.debug_flag:
        set_debug(True)

    if opts.mysql_version:
        manager.set_mysql_version(opts.mysql_version)
        print(bcolors.ok(f"Set MySQL to type '{opts.mysql_version}'"))

    elif opts.install or opts.install_beta:
        manager.unsupported_db_version(opts.force)
        warn_message()
        manager.cl8_save_current()
        manager.cleanup()
        # detect_percona(opts.force, manager)

        # ask user to confirm protectbase plugin disable while beta install
        if not protectbase_warning(opts.install_beta, opts.yes):
            sys.exit(0)

        # remove current packages and install new packages
        if manager.install(opts.install_beta, opts.yes, opts.wizard):
            print("Giving the MySQL service time to start before checking its status (15 sec)")
            time.sleep(15)
        else:
            sys.exit(0) if manager.DISABLED else sys.exit(1)

        # check mysqld service status
        if not manager.ALL_PACKAGES_NEW_NOT_DOWNLOADED and not manager.DISABLED:
            if check_mysqld_is_alive():
                manager.save_installed_version()
                manager.cl8_save_current()
                print(bcolors.ok("Installation of MySQL for db_governor completed"))

            # if sql server failed to start ask user to restore old packages
            elif opts.wizard or opts.yes or query_yes_no(
                    "Installation failed. Restore the previous version?"):
                print(bcolors.fail(
                    "Installation of MySQL for db_governor failed. Restoring the previous MySQL version..."))
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


def detect_percona(force, install_manager_instance):
    """
    Detect unsupported Percona packages
    :param force:
    :param install_manager_instance:
    """
    if force:
        return

    packages = exec_command("""rpm -qa|grep -iE "^percona-" """, silent=True)
    if packages:
        print("Percona packages detected:" + ",".join(packages))
        print("You are running Percona, which is not supported by "
              "MySQL Governor. If you want to run MySQL governor, "
              "we would have to uninstall Percona, and substitute it "
              "by MariaDB or MySQL. Run the following commands to do so:")
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
    print(bcolors.warning(
        "!!!Before making any changing to the database, make sure that you have a reserve copy of users' data!!!"
    ))
    print(bcolors.fail(
        "!!!!!!!!!!!!!!!!!!!!!!!!!!Ctrl+C for cancellation of installation!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    ))
    print(bcolors.ok(
        "Instruction: how to create a whole-database backup - "
        f"{bcolors.OKBLUE}http://docs.cloudlinux.com/index.html?backing_up_mysql.html"
    ))
    time.sleep(10)


def protectbase_warning(beta, yes):
    """
    If protectbase config detected, warn user about protectbase plugin disable in case of --install-beta flag
    and wait for confirmation
    :param beta: --install-beta flag
    :param yes: --yes flag
    :return: True or False, regarding user choice
    """
    if beta and os.path.exists('/etc/yum/pluginconf.d/protectbase.conf'):
        print(bcolors.warning(
            "\nYou are trying to install database related packages from the BETA repo."
            "However, it appears that you have yum's protectbase plugin configured."
            "In order to proceed with the installation, the plugin must be disabled."
            "The plugin will be disabled during the package installation process only."
        ))
        if not yes:
            if not query_yes_no("Do you confirm this action?"):
                return False
    return True


if "__main__" == __name__:
    main(sys.argv[1:])
