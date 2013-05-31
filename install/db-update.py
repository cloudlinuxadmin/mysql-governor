#!/usr/bin/python

import os
import pprint 
import sys
import getopt
import shutil
import stat
import glob
import grp
import pwd
import yum

import lve_diagnostic
from lve_diagnostic import *
import copy_directory
from copy_directory import *
import exec_command
from exec_command import *
import mysql_lib
from mysql_lib import *
from pwd import getpwnam  
from grp import getgrnam  
from distutils import version

SOURCE="/usr/share/lve/dbgovernor/"
clMySQL_list="cl-MySQL-bench cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared"
clMariaDB_list="cl-mariadb cl-mariadb-bench cl-mariadb-devel cl-mariadb-libs cl-mariadb-server"
clCleanMySQL_list="mysql mysql-server mysql-bench mysql-shared mysql-libs"

def get_cl_num():
    result = exec_command("rpm -q --qf \"%{version}\n\" `rpm -q --whatprovides /etc/redhat-release`")
    return result[0]

def upd_mysql():
	if cp.name == "Plesk" and verCompare (cp.version, "10") >= 0:
		if os.path.exists("/usr/share/lve/dbgovernor/mysql.type"):
		    fline=open("/usr/share/lve/dbgovernor/mysql.type").readline().rstrip()
		    if fline=="mysql50" or fline=="mysql51" or fline=="mysql55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    elif fline=="mariadb55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    else:
			exec_command_out("/usr/bin/yum update "+clCleanMySQL_list+" --enablerepo=mysql --nogpgcheck -y")
		else:
		    exec_command_out("/usr/bin/yum update "+clCleanMySQL_list+" --enablerepo=mysql --nogpgcheck -y")
	elif cp.name == "cPanel":
		if os.path.exists("/usr/share/lve/dbgovernor/mysql.type"):
		    fline=open("/usr/share/lve/dbgovernor/mysql.type").readline().rstrip()
		    if fline=="mysql50" or fline=="mysql51" or fline=="mysql55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    elif fline=="mariadb55":
			exec_command_out("/usr/bin/yum update -y "+clMariaDB_list+" --nogpgcheck --disableexcludes=all")
		    else:
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		else:
		    exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
	elif cp.name == "InterWorx":
		if os.path.exists("/usr/share/lve/dbgovernor/mysql.type"):
		    fline=open("/usr/share/lve/dbgovernor/mysql.type").readline().rstrip()
		    if fline=="mysql50" or fline=="mysql51" or fline=="mysql55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    elif fline=="mariadb55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    else:
			exec_command_out("/usr/bin/yum update "+clCleanMySQL_list+" --enablerepo=mysql --nogpgcheck -y")
		else:
		    exec_command_out("/usr/bin/yum update "+clCleanMySQL_list+" --enablerepo=mysql --nogpgcheck -y")
	elif cp.name == "ISPManager":
		if os.path.exists("/usr/share/lve/dbgovernor/mysql.type"):
		    fline=open("/usr/share/lve/dbgovernor/mysql.type").readline().rstrip()
		    if fline=="mysql50" or fline=="mysql51" or fline=="mysql55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    elif fline=="mariadb55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    else:
			exec_command_out("/usr/bin/yum update "+clCleanMySQL_list+" --enablerepo=mysql --nogpgcheck -y")
		else:
		    exec_command_out("/usr/bin/yum update "+clCleanMySQL_list+" --enablerepo=mysql --nogpgcheck -y")
	elif cp.name == "DirectAdmin":
		if os.path.exists("/usr/share/lve/dbgovernor/mysql.type"):
		    fline=open("/usr/share/lve/dbgovernor/mysql.type").readline().rstrip()
		    if fline=="mysql50" or fline=="mysql51" or fline=="mysql55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    elif fline=="mariadb55":
			exec_command_out("/usr/bin/yum update -y "+clMariaDB_list+" --nogpgcheck --disableexcludes=all")
		    else:
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		else:
		    exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
	else:
		if os.path.exists("/usr/share/lve/dbgovernor/mysql.type"):
		    fline=open("/usr/share/lve/dbgovernor/mysql.type").readline().rstrip()
		    if fline=="mysql50" or fline=="mysql51" or fline=="mysql55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    elif fline=="mariadb55":
			exec_command_out("/usr/bin/yum update -y "+clMySQL_list+" --nogpgcheck --disableexcludes=all")
		    else:
			exec_command_out("/usr/bin/yum update "+clCleanMySQL_list+" --enablerepo=mysql --nogpgcheck -y")
		else:
		    exec_command_out("/usr/bin/yum update "+clCleanMySQL_list+" --enablerepo=mysql --nogpgcheck -y")


cp = get_cp()
upd_mysql()
