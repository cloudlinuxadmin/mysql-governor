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

def getItem(txt1, txt2, op):
	try:
    		i1 = int(txt1)
	except ValueError:
    		i1 = -1
	try:
    		i2 = int(txt2)
	except ValueError:
    		i2 = -1
	if i1 == -1 or i2 == -1:
		if op == 0:
			return txt1>txt2
		else:
			return txt1<txt2
	else:
		if op == 0:
			return i1>i2
		else:
			return i1<i2

#Compare version of types xx.xx.xxx... and yyy.yy.yy.y..
#if xxx and yyy is numbers, than comapre as numbers
#else - comapre as strings
def verCompare (base, test):
	base = base.split(".")
	test = test.split(".")
	if(len(base)>len(test)):
		ln = len(test)
	else:
		ln = len(base)
	for i in range(ln):
		if getItem(base[i],test[i],0):
			return 1
		if getItem(base[i],test[i],1):
			return -1
	if len(base)==len(test):	
		return 0
	elif len(base)>len(test):
		return 1
	else:
		return 0


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
