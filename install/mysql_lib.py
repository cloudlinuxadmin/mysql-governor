#!/usr/bin/python

import os

def Execute(str):
    handle = os.popen(str)
    return handle.read()


def install_cagefs_module_plesk():
	mysqlpwd = open('/etc/psa/.psa.shadow', 'r').readline().rstrip()
	mysql_client = "mysql --no-beep --skip-column-names --user=admin --password=" + mysqlpwd + " --execute="
	result = Execute(mysql_client + '"select * from psa.Modules where name=\'plesk-cagefs\'"')
	if result == "":
		Execute(mysql_client + '"insert into psa.Modules(name, packname, display_name, description, icon) '+\
		"values('plesk-cagefs', 'plesk-cagefs', 'CageFS', 'GageFS', "+\
		"'/images/modules/plesk-cagefs/addon_CloudLinux_logo2.png')\"")

def delete_cagefs_module_plesk():
	mysqlpwd = open('/etc/psa/.psa.shadow', 'r').readline().rstrip()
	mysql_client = "mysql --no-beep --skip-column-names --user=admin --password=" + mysqlpwd + " --execute="
	Execute(mysql_client + '"delete from psa.Modules where name=\'plesk-cagefs\'"')
	
