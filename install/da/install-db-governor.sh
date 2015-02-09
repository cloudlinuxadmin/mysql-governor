#!/bin/bash

. /usr/share/lve/dbgovernor/utils/db_install_common.sh

if [ "$1" == "--delete" ]; then
        echo "Removing mysql for db_governor start"

        checkFile "/usr/local/directadmin/custombuild/build"
        /usr/local/directadmin/custombuild/build set mysql_inst yes
        
        rm -f /etc/yum.repos.d/cl-mysql.repo
        /usr/local/directadmin/custombuild/build mysql update
        echo "Removing mysql for db_governor completed"
        exit

fi

echo "Installation mysql for db_governor start"

checkFile "/usr/local/directadmin/custombuild/build"
/usr/local/directadmin/custombuild/build set mysql_inst no

checkFile "/usr/local/directadmin/custombuild/options.conf"
MYSQL_DA_VER=`cat /usr/local/directadmin/custombuild/options.conf | grep mysql= | cut -d= -f2`
mysqlTypeFileSet="/usr/share/lve/dbgovernor/mysql.type";

if [ -f "$mysqlTypeFileSet" ]; then
	MYSQL_VER=`cat $mysqlTypeFileSet`
else
    MYSQL_VER="auto"
fi

if [ "$MYSQL_VER" == "auto" ]; then
    MYSQL_VER=$MYSQL_DA_VER
fi

if [ "$MYSQL_VER" == "5.0" ]; then
    MYSQL_VER="mysql50"
fi 
if [ "$MYSQL_VER" == "5.1" ]; then
    MYSQL_VER="mysql51"
fi 
if [ "$MYSQL_VER" == "5.5" ]; then
    MYSQL_VER="mysql55"
fi 
if [ "$MYSQL_VER" == "5.6" ]; then
    MYSQL_VER="mysql56"
fi 
if [ "$MYSQL_VER" == "10.0.0" ]; then
    MYSQL_VER="mariadb100"
fi 
if [ "$MYSQL_VER" == "10.1.1" ]; then
    MYSQL_VER="mariadb101"
fi 

if [ -e /usr/lib/systemd/system/mysql.service ] || [ -e /etc/systemd/system/mysql.service ]; then
/bin/systemctl stop mysql.service
else
/sbin/service mysql stop
fi

installDb "$MYSQL_VER"

sleep 5;

DACONF_FILE_MYSQL=/usr/local/directadmin/conf/mysql.conf
MYSQLUSER=`grep "^user=" ${DACONF_FILE_MYSQL} | cut -d= -f2`
MYSQLPASSWORD=`grep "^passwd=" ${DACONF_FILE_MYSQL} | cut -d= -f2`

if [ -e /usr/bin/mysql_upgrade ]; then
   /usr/bin/mysql_upgrade --user=${MYSQLUSER} --password=${MYSQLPASSWORD}
elif [ -e /usr/bin/mysql_fix_privilege_tables ]; then
   /usr/bin/mysql_fix_privilege_tables --user=${MYSQLUSER} --password=${MYSQLPASSWORD}
fi

echo "Patch governor configuration file"
checkFile "/etc/container/mysql-governor.xml"
if [ -e /etc/container/mysql-governor.xml ]; then
    IS_LOGIN=`cat /etc/container/mysql-governor.xml | grep login=`
    if [ -z "$IS_LOGIN" ]; then
         sed -e "s/<connector prefix_separator=\"_\"\/>/<connector prefix_separator=\"_\" login=\"$MYSQLUSER\" password=\"$MYSQLPASSWORD\"\/>/" -i /etc/container/mysql-governor.xml
    fi
    
fi

IS_GOVERNOR=`rpm -qa governor-mysql`
if [ -n "$IS_GOVERNOR" ]; then
	if [ -e /usr/lib/systemd/system/db_governor.service ] || [ -e /etc/systemd/system/db_governor.service ]; then
	    /bin/systemctl restart db_governor.service
	else
	    /sbin/service db_governor restart
	fi
	echo "DB-Governor installed/updated...";
fi

echo "Installation mysql for db_governor completed"
echo "Rebuild php please... /usr/local/directadmin/custombuild/build php"
