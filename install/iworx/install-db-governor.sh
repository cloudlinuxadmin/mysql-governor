#!/bin/bash

function checkFile(){
	if [ ! -e "$1" ]; then
		echo "Installtion error file ---$1---- does not exists"
		exit 1
	fi
}


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

CL=`echo -n "cl5"`
CL6=`uname -a | grep "\.el6\."`
if [ -n "$CL6" ]; then
    CL=`echo -n "cl6"`
    if [ -e /etc/my.cnf ]; then
        sed '/userstat/d' -i /etc/my.cnf
        sed '/userstat_running/d' -i /etc/my.cnf
    fi
fi

wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysql.repo


yum install mysql mysql-server mysql-bench mysql-shared mysql-libs --enablerepo=mysql --nogpgcheck -y
if [ ! -e /etc/my.cnf.bkp ]; then
    cp -f /etc/my.cnf /etc/my.cnf.bkp
fi
sed /userstat/d -i /etc/my.cnf
/sbin/service mysqld restart
echo "Giving mysqld a few seconds to start up...";
sleep 5;

MYSQLUSER="iworx"
MYSQLPASSWORD=`cat /home/interworx/iworx.ini | grep rootdsn= | cut -d"/" -f3 | cut -d: -f2 | cut -d@ -f1`
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
	/sbin/service db_governor restart
	echo "DB-Governor installed/updated...";
fi

echo "Installation mysql for db_governor completed"
