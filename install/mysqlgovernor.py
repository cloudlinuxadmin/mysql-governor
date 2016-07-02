#!/opt/alt/python27/bin/python2.7
#coding:utf-8
import argparse
import sys
import time

from clcommon import cpapi

from modules import InstallManager
from utilities import exec_command, bcolors, query_yes_no


def build_parser():
    """
    Build CLI parser
    """
    parser = argparse.ArgumentParser(prog="install-mysql", add_help=True,
                                     description="Use following syntax to manage DBGOVERNOR install utility:")
    parser.add_argument("--verbose", help="switch verbose level on",
                        dest="verbose", action="store_true", default=False)
    parser.add_argument("--mysql-version", help="select MySQL version for db-governor. Available mysql types: auto, mysql50, mysql51, mysql55, mysql56, mysql57, mariadb55, mariadb100, mariadb101",
                        dest="mysql_version", required=False)
    parser.add_argument("-i", "--install", help="install MySQL for db-governor",
                        dest="install", action="store_true", default=False)
    parser.add_argument("-d", "--delete", help="delete MySQL for db-governor",
                        dest="delete", action="store_true", default=False)
    parser.add_argument("--install-beta", help="install MySQL beta for governor or update beta if exists newer beta version",
                        dest="install_beta", action="store_true", default=False)
    parser.add_argument("-c", "--clean-mysql", help="clean MySQL packages list (after governor installation)",
                        dest="clean_mysql", action="store_true", default=False)
    parser.add_argument("-m", "--clean-mysql-delete", help="clean cl-MySQL packages list (after governor deletion)",
                        dest="clean_mysql_delete", action="store_true", default=False)
    parser.add_argument("-t", "--dbupdate", help="update UserMap file",
                        dest="dbupdate", action="store_true", default=False)
    parser.add_argument("--fix-cpanel-hooks", help="fix adduser and deluser hooks for cPanel",
                        dest="fix_cpanel_hooks", action="store_true", default=False)
    parser.add_argument("--fix-cpanel-cl-mysql", help="fix mysqld service for cPanel(CL7)",
                        dest="fix_cpanel_cl_mysql", action="store_true", default=False)
    # parser.add_argument("-s", "--safe-install", help="show which vesrion of MySQL/MariaDB will be installed before installation",
    #                     dest="safe_install", action="store_true", default=False)
    parser.add_argument("--force", help="Don`t exit if percona installation found",
                        dest="force", action="store_true", default=False)
    parser.add_argument("-u", "--upgrade", help="Option is deprecated. Use `yum update` instead",
                        dest="upgrade", action="store_true", default=False)
    parser.add_argument("--update-mysql-beta", help="Option is deprecated. Use --install-beta instead",
                        dest="update_mysql_beta", action="store_true", default=False)
    parser.add_argument("--fs-suid", help="Helper utility", dest="fs_suid",
                        action="store_true", default=False)
    return parser


def main(argv):
    """
    Run main actions
    """
    parser = build_parser()
    if not argv:
        parser.print_help()
        sys.exit(2)

    opts = parser.parse_args(argv)

    # create install manager instance for current cp
    manager = InstallManager.factory(cpapi.CP_NAME)

    if opts.install or opts.install_beta:
        warn_message()
        # if opts.safe_install:
        #     safe_mysql_op()
        detect_percona(opts.force)

        # remove current packages and install new packages
        manager.install(opts.install_beta)

        # check mysqld service status
        if exec_command("ps -Af | grep -v grep | grep mysqld | grep datadir",
                        True, silent=True):
            manager.save_installed_version()
            print "Installation mysql for db_governor completed"
        
        # if sql server failed to start ask user to restore old packages
        elif query_yes_no("Installation is failed. Restore previous version?"):
            print "Installation mysql for db_governor was failed. Restore previous mysql version"
            manager.install_rollback(opts.install_beta)

        manager.cleanup()

    elif opts.delete:
        manager.delete()
        print "Deletion is complete"

        # if exec_command("ps -Af | grep -v grep | grep mysqld | grep datadir",
                        # True, silent=True):
            # manager.cleanup()
        # else:
            # print "Deletion is failed"
        # elif query_yes_no("Deletion is failed. Restore previous version?"):
            # manager.delete_rollback()

        manager.cleanup()

    elif opts.mysql_version:
        manager.set_mysql_version(opts.mysql_version)
        print "Now set MySQL to type '%s'" % opts.mysql_version
    elif opts.dbupdate:
        manager.update_user_map_file()
    elif opts.fix_cpanel_hooks:
        manager.install_mysql_beta_testing_hooks()
    elif opts.fix_cpanel_cl_mysql:
        manager.fix_cl7_mysql()
    elif opts.clean_mysql:
        print "Option is deprecated."
    elif opts.clean_mysql_delete:
        print "Option is deprecated."
    elif opts.upgrade:
        print "Option is deprecated. Use `yum update` instead."
    elif opts.update_mysql_beta:
        print "Option is deprecated. Use --install-beta instead."
    elif opts.fs_suid:
        manager.set_fs_suid_dumpable()
    else:
        parser.print_help()
        sys.exit(2)


def detect_percona(force):
    if force:
        return None

    packages = exec_command("""rpm -qa|grep -iE "^percona-" """, silent=True)
    if len(packages):
        print "Percona packages deteced:" + ",".join(packages)
        print "You are running Percona, which is not supported by MySQL Governor. If you want to run MySQL governor, we would have to uninstall Percona,and substitute it for MariaDB or MySQL. Run installator next commands for install:"
        print InstallManager._rel("mysqlgovernor.py")+" --mysql-version=mysql56 (or mysql50, mysql51, mysql55, mysql57, mariadb55, mariadb100, mariadb101)"
        print InstallManager._rel("mysqlgovernor.py")+" --install --force"
        sys.exit(2)


# def safe_mysql_op():
#     result = "None"
#     cp_name = cpapi.CP_NAME  
#     print "Will be installed MySQL/MariaDB version(detected by governor): "
#     if cp_name == "Plesk":  #  and verCompare(cp.version, "10") >= 0:
#         result = exec_command(SOURCE+"plesk/install-db-governor-version.sh")
#     elif cp_name == "cPanel":
#         result = exec_command(SOURCE+"cpanel/install-db-governor-version")
#     elif cp_name == "InterWorx":
#         result = exec_command(SOURCE+"iworx/install-db-governor-version.sh")
#     elif cp_name == "ISPManager":    
#         result = exec_command(SOURCE+"ispmanager/install-db-governor-version.sh")
#     elif cp_name == "DirectAdmin":
#         result = exec_command(SOURCE+"da/install-db-governor-version.sh")
#     else:
#         result = exec_command(SOURCE+"other/install-db-governor-version.sh")

#     if result[0] == "mysql50":
#         print "MySQL 5.0"
#     elif result[0] == "mysql51":
#         print "MySQL 5.1"
#     elif result[0] == "mysql55":
#         print "MySQL 5.5"
#     elif result[0] == "mysql56":
#         print "MySQL 5.6"
#     elif result[0] == "mysql57":
#         print "MySQL 5.7"
#     elif result[0] == "mariadb55":
#         print "MariaDB 5.5"
#     elif result[0] == "mariadb100":
#         print "MariaDB 10.0"
#     elif result[0] == "mariadb101":
#         print "MariaDB 10.1"
#     else:
#         print "Unknown"
#         print "Type please: "+SOURCE+"db-select-mysql --mysql-version=<mysql50, mysql51, mysql55, mysql56, mysql57, maridb55, maridb100, mariadb101>"
#         sys.exit(2)

#     print "auto means will be installed mysql-server package from CloudLinux repo"
#     print "If you don't agree - press n and type: "+SOURCE+"db-select-mysql --mysql-version=<mysql50, mysql51, mysql55, mysql56, mysql57, maridb55, maridb100, mariadb101>"
#     if query_yes_no("Should we continue installation?", "yes") == False:
#         sys.exit(2)


def warn_message():
    print bcolors.WARNING + "!!!Before making any changing with database make sure that you have reserve copy of users data!!!"+ bcolors.ENDC
    print bcolors.FAIL + "!!!!!!!!!!!!!!!!!!!!!!!!!!Ctrl+C for cancellation of installation!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"+ bcolors.ENDC
    print bcolors.OKGREEN + "Instruction: how to create whole database backup - " + bcolors.OKBLUE +"http://docs.cloudlinux.com/index.html?backing_up_mysql.html"+ bcolors.ENDC
    time.sleep(10)


if "__main__" == __name__:
    main(sys.argv[1:])
