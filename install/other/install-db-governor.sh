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
	
	installDb "auto"
	
	exit
fi

echo "Installation mysql for db_governor start"

if [ -f "$mysqlTypeFileSet" ]; then
  SQL_VERSION_=`cat $mysqlTypeFileSet`
else
  SQL_VERSION_="auto"
fi

installDb "$SQL_VERSION_"
