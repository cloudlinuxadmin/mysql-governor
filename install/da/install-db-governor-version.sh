#!/bin/bash

. /usr/share/lve/dbgovernor/utils/db_install_common.sh

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


echo -n "$MYSQL_VER"

