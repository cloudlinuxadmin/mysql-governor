#!/opt/alt/python37/bin/python3
# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
import sys
import os
from modules import InstallManager

def main(argv):
    #write_extended it is needed for the exec_command in the InstallManager
    sys.stdout.write_extended = lambda x: None
    sys.stderr.write_extended = lambda x: None

    mysql_ver = None
    if argv:
        mysql_ver = argv[0]
    else:
        mysql_ver = InstallManager._check_mysql_version().get('full')

    print("Fixing drop-in files for '%s'" % mysql_ver)

    #delete all governor's dropin
    if os.path.exists("/etc/systemd/system/mariadb.service.d/governor.conf"):
        os.unlink("/etc/systemd/system/mariadb.service.d/governor.conf")
    if os.path.exists("/etc/systemd/system/mysqld.service.d/governor.conf"):
        os.unlink("/etc/systemd/system/mysqld.service.d/governor.conf")
    if os.path.exists("/etc/systemd/system/mysql.service.d/governor.conf"):
        os.unlink("/etc/systemd/system/mysql.service.d/governor.conf")

    if os.path.exists("/etc/systemd/system/mariadb.service.d/gov.conf"):
        os.unlink("/etc/systemd/system/mariadb.service.d/gov.conf")
    if os.path.exists("/etc/systemd/system/mysqld.service.d/gov.conf"):
        os.unlink("/etc/systemd/system/mysqld.service.d/gov.conf")

    #create one dropin only
    if mysql_ver and mysql_ver.startswith("maria"):
        os.makedirs("/etc/systemd/system/mariadb.service.d", 0o755, True)
        os.symlink("/usr/share/lve/dbgovernor/governor.conf", "/etc/systemd/system/mariadb.service.d/gov.conf")
    elif mysql_ver and mysql_ver.startswith("mysql"):
        os.makedirs("/etc/systemd/system/mysqld.service.d", 0o755, True)
        os.symlink("/usr/share/lve/dbgovernor/governor.conf", "/etc/systemd/system/mysqld.service.d/gov.conf")

    os.system('systemctl daemon-reload')

if "__main__" == __name__:
    main(sys.argv[1:])
