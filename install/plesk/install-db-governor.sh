#!/bin/bash

mysqlTypeFileSet="/usr/share/lve/dbgovernor/mysql.type"

function checkFile(){
	if [ ! -e "$1" ]; then
		echo "Installtion error file ---$1---- does not exists"
		exit 1
	fi
}

function installDb(){
	SQL_VERSION=$1
	
	CL=`echo -n "cl5"`
	CL6=`uname -a | grep "\.el6\."`
	if [ -n "$CL6" ]; then
	    CL=`echo -n "cl6"`
	    if [ -e /etc/my.cnf ]; then
        	sed '/userstat/d' -i /etc/my.cnf
	        sed '/userstat_running/d' -i /etc/my.cnf
	    fi
	fi

	if [ "$SQL_VERSION" == "auto" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysql.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install mysql mysql-server mysql-bench mysql-shared mysql-libs --enablerepo=mysql --nogpgcheck -y
	fi
	if [ "$SQL_VERSION" == "mysql50" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/cl-mysql-beta-5.0.repo
	  if [ -e /usr/libexec/mysqld ]; then
	    mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-bench cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y
	fi
	if [ "$SQL_VERSION" == "mysql51" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/cl-mysql-beta.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y
	fi
	if [ "$SQL_VERSION" == "mysql55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/cl-mysql-beta-5.5.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y
	fi
	if [ "$SQL_VERSION" == "mariadb55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/cl-mariadb-5.5.repo
	  yum install cl-mariadb cl-mariadb-bench cl-mariadb-devel cl-mariadb-libs cl-mariadb-server --nogpgcheck -y
	fi

	if [ ! -e /etc/my.cnf.bkp ]; then
	    cp -f /etc/my.cnf /etc/my.cnf.bkp
	fi
	sed /userstat/d -i /etc/my.cnf
	/sbin/service mysqld restart
	echo "Giving mysqld a few seconds to start up...";
	sleep 5;

	IS_GOVERNOR=`rpm -qa governor-mysql`
	if [ -n "$IS_GOVERNOR" ]; then
		/sbin/service db_governor restart
		echo "DB-Governor installed/updated...";
	fi

	echo "Installation mysql for db_governor completed"
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

if [ -f "$mysqlTypeFileSet" ]; then
  SQL_VERSION_=`cat $mysqlTypeFileSet`
else
  SQL_VERSION_="auto"
fi

installDb "$SQL_VERSION_"

MYSQLUSER="admin"
MYSQLPASSWORD=`cat /etc/psa/.psa.shadow`
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
	/sbin/service db_governor restart
	echo "DB-Governor installed/updated...";
fi

echo "Installation mysql for db_governor completed"
