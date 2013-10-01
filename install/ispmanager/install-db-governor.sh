#!/bin/bash

. /usr/share/lve/dbgovernor/utils/db_install_common.sh

if [ "$1" == "--delete" ]; then
	echo "Removing mysql for db_governor start"
	checkFile "/etc/my.cnf"
	VERSION=`mysql --version | awk '{ print $5 }' | cut -d. -f1,2`
	if [ ! -e /etc/my.cnf.bkp ]; then
	    cp -f /etc/my.cnf /etc/my.cnf.bkp
	fi
	if [ "$VERSION" != "5.0" ]; then
	    if [ "$VERSION" != "5.1" ]; then
		IS_OPT=`cat /etc/my.cnf | grep userstat`
		if [ -z "$IS_OPT" ]; then
		    sed -e "s/\[mysqld\]/\[mysqld\]\nuserstat=0\n/" -i /etc/my.cnf
		fi    
	    else
		if [ -e /etc/my.cnf ]; then
		    sed '/userstat/d' -i /etc/my.cnf
		    sed '/userstat_running/d' -i /etc/my.cnf
		fi
	    fi
	else
	    IS_OPT=`cat /etc/my.cnf | grep userstat`
	    if [ -z "$IS_OPT" ]; then
		sed -e "s/\[mysqld\]/\[mysqld\]\nuserstat_running=0\n/" -i /etc/my.cnf
	    fi
	fi
	/sbin/service mysqld restart
        mv -f /etc/yum.repos.d/cl-mysql.repo /etc/yum.repos.d/cl-mysql.repo.bak
	echo "Removing mysql for db_governor completed"
	exit
fi

echo "Installation mysql for db_governor start"

if [ -f "$mysqlTypeFileSet" ]; then
  SQL_VERSION_=`cat $mysqlTypeFileSet`
else
  SQL_VERSION_="auto"
fi

installDb "$SQL_VERSION_"


MYSQLUSER="root"
MYSQLPASSWORD=`cat /usr/local/ispmgr/etc/ispmgr.conf | sed -n '/DbServer "MySQL"/,/SupportCenterServer/p' | sed -n '/Password /p' | sed '/Change/d' | tr -d '\n' | cut -d" " -f2`

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
        sed -e "s/<connector prefix_separator=\"_\"\/>/<connector prefix_separator=\"_\" login=\"$MYSQLUSER\" password=\"$(echo $MYSQLPASSWORD | sed -e 's/\([[\/.*]\|\]\)/\\&/g')\"\/>/" -i /etc/container/mysql-governor.xml
    fi
    
fi

IS_GOVERNOR=`rpm -qa governor-mysql`
if [ -n "$IS_GOVERNOR" ]; then
	/sbin/service db_governor restart
	echo "DB-Governor installed/updated...";
fi

echo "Installation mysql for db_governor completed"
