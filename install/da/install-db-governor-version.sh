#!/bin/bash

. /usr/share/lve/dbgovernor/utils/db_install_common.sh

checkFile "/usr/local/directadmin/custombuild/options.conf"
MYSQL_DA_VER=`cat /usr/local/directadmin/custombuild/options.conf | grep mysql= | cut -d= -f2`
mysqlTypeFileSet="/usr/share/lve/dbgovernor/mysql.type";



MYSQL_DA_TYPE=`cat /usr/local/directadmin/custombuild/options.conf | grep mysql_inst= | cut -d= -f2`
if [ -e /usr/share/lve/dbgovernor/da.tp.old ]; then
  da_old=`cat /usr/share/lve/dbgovernor/da.tp.old`
  if [ "$MYSQL_DA_TYPE" == "no" ]; then
    MYSQL_DA_TYPE=`echo "$da_old"`
  fi
fi
MYSQL_TP="set"

if [ -f "$mysqlTypeFileSet" ]; then
	MYSQL_VER=`cat $mysqlTypeFileSet`
	MYSQL_TP="set"
else
    MYSQL_VER="auto"
    MYSQL_TP="unset"
fi

if [ "$MYSQL_VER" == "auto" ]; then
    MYSQL_VER=$MYSQL_DA_VER
fi

if [ "$MYSQL_TP" == "set" ]; then
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
else
   if [ "$MYSQL_DA_TYPE" == "mysql" ]; then
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
   fi
   if [ "$MYSQL_DA_TYPE" == "mariadb" ]; then
    if [ "$MYSQL_VER" == "10.1" ]; then
      MYSQL_VER="mariadb101"
    fi 
    if [ "$MYSQL_VER" == "10.0" ]; then
      MYSQL_VER="mariadb100"
    fi 
    if [ "$MYSQL_VER" == "5.5" ]; then
      MYSQL_VER="mariadb55"
    fi
    if [ "$MYSQL_VER" == "10.0.0" ]; then
      MYSQL_VER="mariadb100"
    fi 
    if [ "$MYSQL_VER" == "10.1.1" ]; then
      MYSQL_VER="mariadb101"
    fi
   fi
fi


echo -n "$MYSQL_VER"

