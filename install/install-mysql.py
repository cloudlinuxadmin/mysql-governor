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

def get_cl_num():
    result = exec_command("rpm -q --qf \"%{version}\n\" `rpm -q --whatprovides /etc/redhat-release`")
    return result[0]

def recursive_file_permissions(path,uid=-1,gid=-1):
	for item in glob.glob(path+'/*'):
		if os.path.isdir(item):
			recursive_file_permissions(os.path.join(path,item),uid,gid)
		else:
			try:
				os.chown(os.path.join(path,item),uid,gid)
			except:
				print('File permissions on {0} not updated due to error.')


def touch(fname):
	try:
		os.utime(fname, None)
	except:
		open(fname, 'a').close()


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


def usage():
	print ''                                                                                                                                             
        print 'Use following syntax to manage DBGOVERNOR istall utility:'                                                                                                       
        print sys.argv[0]+" [OPTIONS]"                                                                                                                       
        print 'Options:'                                                                                                                                     
        print " -i | --install             : instal MySQL for db-governor"                                                                 
        print " -d | --delete              : delete MySQL for db-governor"                                                                  
	print "    | --install-beta        : install MySQL 5.1.63 beta   "
	print " -c | --clean-mysql         : clean MySQL packages list (after governor installation)"
	print " -m | --clean-mysql-delete  : clean cl-MySQL packages list (after governor deletion)"

def install_mysql():
	if cp.name == "Plesk" and verCompare (cp.version, "10") >= 0:
		exec_command_out(SOURCE+"plesk/install-db-governor.sh --install")
	elif cp.name == "cPanel":
		# install hook for CPanel to patch Apache's suexec and suphp
		exec_command_out(SOURCE+"cpanel/db_governor-clear-old-hook")
		exec_command_out(SOURCE+"cpanel/install-db-governor --force")		
	elif cp.name == "InterWorx":
		exec_command_out(SOURCE+"iworx/install-db-governor.sh --install")
	elif cp.name == "ISPManager":	
		exec_command_out(SOURCE+"ispmanager/install-db-governor.sh --install")
	elif cp.name == "DirectAdmin":
		exec_command_out(SOURCE+"da/install-db-governor.sh --install")
	else:
		print "Current panel unsupported. Panel name: "+cp.name+" version: "+cp.version


def install_mysql_beta():
        exec_command_out(SOURCE+"other/set_fs_suid_dumpable.sh")
	if cp.name == "Plesk" and verCompare (cp.version, "10") >= 0:
		exec_command_out(SOURCE+"plesk/install-db-governor.sh --install")
	elif cp.name == "cPanel":
		# install hook for CPanel to patch Apache's suexec and suphp
		exec_command_out(SOURCE+"cpanel/db_governor-clear-old-hook")
		exec_command_out(SOURCE+"cpanel/install-db-governor-beta")
                exec_command_out(SOURCE+"cpanel/install-mysql-disabler.sh")
                exec_command_out(SOURCE+"cpanel/cpanel-install-hooks")		
                exec_command_out(SOURCE+"cpanel/upgrade-mysql-disabler.sh")
	elif cp.name == "InterWorx":
		exec_command_out(SOURCE+"iworx/install-db-governor.sh --install")
	elif cp.name == "ISPManager":	
		exec_command_out(SOURCE+"ispmanager/install-db-governor.sh --install")
	elif cp.name == "DirectAdmin":
		exec_command_out(SOURCE+"da/install-db-governor.sh --install")
	else:
                exec_command_out(SOURCE+"other/install-db-governor.sh --install")


def delete_mysql():
	if cp.name == "Plesk" and verCompare (cp.version, "10") >= 0:		
                exec_command_out(SOURCE+"plesk/install-db-governor.sh --delete")
	elif cp.name == "cPanel":
                exec_command_out(SOURCE+"cpanel/cpanel-delete-hooks")
		if os.path.exists("/etc/mysqlupdisable"):
			os.remove("/etc/mysqlupdisable")
                if os.path.exists("/var/cpanel/rpm.versions.d/cloudlinux.versions"):
			os.remove("/var/cpanel/rpm.versions.d/cloudlinux.versions")
                if os.path.exists("/etc/cpupdate.conf.governor"):
                        if os.path.exists("/etc/cpupdate.conf"):
                                os.remove("/etc/cpupdate.conf")
                        os.rename("/etc/cpupdate.conf.governor", "/etc/cpupdate.conf")
                if version.LooseVersion(cp.version) < version.LooseVersion("11.36"):
		        exec_command_out("/scripts/mysqlup --force")
                else:
                        exec_command_out("/scripts/upcp --force")
                if os.path.exists("/scripts/check_cpanel_rpms"):
                        exec_command_out("/scripts/check_cpanel_rpms --fix --targets=MySQL50,MySQL51,MySQL55")
	elif cp.name == "InterWorx":		
                exec_command_out(SOURCE+"iworx/install-db-governor.sh --delete")
	elif cp.name == "ISPManager":
                exec_command_out(SOURCE+"ispmanager/install-db-governor.sh --delete")
	elif cp.name == "DirectAdmin":
		exec_command_out(SOURCE+"da/install-db-governor.sh --delete")
	else:
                exec_command_out(SOURCE+"other/install-db-governor.sh --delete")


def cp_supported():
	if cp.name == "Plesk" and verCompare (cp.version, "10") >= 0:		
		return True
	if cp.name in ("cPanel", "InterWorx", "ISPManager", "DirectAdmin"):
		return True
	return False

def remove_specific_package(pname, yb):
        print "Looking for " + pname
	if yb.rpmdb.searchNevra(name=pname):
	    exec_command_out("rpm -e --justdb " + pname)
	else:
	    print pname + " not installed"

def remove_sepcific_mysql(mname, yb):
        remove_specific_package(mname + "-server", yb)
        remove_specific_package(mname + "-shared", yb)
        remove_specific_package(mname + "-devel", yb)
        remove_specific_package(mname + "-bench", yb)
        remove_specific_package(mname + "-test", yb)
        remove_specific_package(mname + "-client", yb)

def remove_mysql_justdb():
	yb = yum.YumBase()
        remove_sepcific_mysql('cpanel-MySQL', yb)
        remove_sepcific_mysql('MySQL', yb)
        remove_sepcific_mysql('MySQL50', yb)
        remove_sepcific_mysql('MySQL51', yb)
        remove_sepcific_mysql('MySQL55', yb)
	print "Cleaning of MySQL packages completed"

def remove_mysql_justdb_cl():
	yb = yum.YumBase()
        remove_sepcific_mysql('cl-MySQL', yb)
	print "Cleaning of cl-MySQL packages completed"

def delete_governor_rpm():
    exec_command_out("rpm -e governor-mysql")

def set_bad_lve_container():
    if os.path.exists("/usr/sbin/lvectl"):
	clver = get_cl_num()
	result = exec_command("/usr/sbin/lvectl limits 3")
	if len(result)==1:
	    if clver=="5":
		exec_command_out("/usr/sbin/lvectl set 3 --cpu=25 --ncpu=1 --io=1024 --mem=0 --vmem=0 --maxEntryProcs=0 --save-all-parameters")
	    else:
    		exec_command_out("/usr/sbin/lvectl set 3 --cpu=25 --ncpu=1 --io=1024 --nproc=0 --pmem=0 --mem=0 --vmem=0 --maxEntryProcs=0 --save-all-parameters")  
    	    return
	result1 = exec_command("/usr/sbin/lvectl limits 3 | sed -n 2p | sed -e 's/\s\+/ /g' | cut -d' ' -f7")
	result2 = exec_command("/usr/sbin/lvectl limits default | sed -n 2p | sed -e 's/\s\+/ /g' | cut -d' ' -f7")
	if result1 == result2:
	    if clver=="5":
		exec_command_out("/usr/sbin/lvectl set 3 --cpu=25 --ncpu=1 --io=1024 --mem=0 --vmem=0 --maxEntryProcs=0 --save-all-parameters")
	    else:
    		exec_command_out("/usr/sbin/lvectl set 3 --cpu=25 --ncpu=1 --io=1024 --nproc=0 --pmem=0 --mem=0 --vmem=0 --maxEntryProcs=0 --save-all-parameters")

def remove_repo_file():
        if os.path.exists("/etc/yum.repos.d/cl-mysql.repo"):
                os.remove("/etc/yum.repos.d/cl-mysql.repo") 

cp = get_cp()
try:
	opts, args = getopt.getopt(sys.argv[1:], "hidcm", ["help", "install", "delete", "install-beta", "clean-mysql", "clean-mysql-delete"])
except getopt.GetoptError, err:
	# print help information and exit:
	print str(err) # will print something like "option -a not recognized"
	usage()
	sys.exit(2)
	                                                          
for o, a in opts:
	if o in ("-h", "--help"):
		usage()
		sys.exit()
	elif o in ("-i", "--install"):
		install_mysql_beta()
		remove_mysql_justdb()
                set_bad_lve_container()
	elif o in ("-d", "--delete"):
                remove_repo_file()
		remove_mysql_justdb_cl()
                delete_mysql()
                delete_governor_rpm()
	elif o in ("--install-beta",):
                print "Option is deprecated. Use --install instead"
	elif o in ("c", "--clean-mysql"):
                remove_mysql_justdb()
	elif o in ("m", "--clean-mysql-delete"):
		remove_mysql_justdb_cl()
	else:
		usage()
		sys.exit(2)