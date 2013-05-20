#!/bin/bash

mysqlTypeFileSet="/usr/share/lve/dbgovernor/mysql.type"

function checkFile(){
	if [ ! -e "$1" ]; then
		echo "Installtion error file ---$1---- does not exists"
		exit 1
	fi
}

#if [ "${MYSQL_OPT}" == "5.5" ]; then
#    echo "MySQL 5.5 not patched yet"
#    exit
#fi

if [ -f "$mysqlTypeFileSet" ]; then
	SQL_VERSION=`cat $mysqlTypeFileSet`
else
	SQL_VERSION="auto"
fi

if [ "$1" == "--delete" ]; then
	echo "Removing mysql for db_governor start"

	checkFile "/usr/local/directadmin/custombuild/build"
	/usr/local/directadmin/custombuild/build set mysql_inst yes
	
	NAME_DB="MySQL"

	rpm -e --justdb cl-${NAME_DB}-devel
	rpm -e --justdb cl-${NAME_DB}-bench
	rpm -e --justdb cl-${NAME_DB}-server
	rpm -e --justdb cl-${NAME_DB}-shared
	rpm -e --justdb cl-${NAME_DB}-test
	rpm -e --justdb cl-${NAME_DB}-client
	rpm -e --justdb cl-mariadb-devel
	rpm -e --justdb cl-mariadb-bench
	rpm -e --justdb cl-mariadb-server
	rpm -e --justdb cl-mariadb-libs
	rpm -e --justdb cl-mariadb-test
	rpm -e --justdb cl-mariadb
	rm -f /etc/yum.repos.d/cl-mysql.repo
	/usr/local/directadmin/custombuild/build mysql update
	echo "Removing mysql for db_governor completed"
	exit
fi

echo "Installation mysql for db_governor start"

checkFile "/usr/local/directadmin/custombuild/build"
/usr/local/directadmin/custombuild/build set mysql_inst no

if [ -e /etc/init.d/mysqld ]; then
	cp -f /etc/init.d/mysqld /etc/init.d/mysqld.bkp
fi
MSQL_OPT_OLD=`mysql --version | awk '{ print $5 }' | cut -d. -f1,2`
checkFile "/usr/local/directadmin/custombuild/options.conf"
MYSQL_OPT=`cat /usr/local/directadmin/custombuild/options.conf | grep mysql= | cut -d= -f2`
if [ "$MSQL_OPT_OLD" != "$MYSQL_OPT" ]; then
	NAME_DB="MySQL"

	rpm -e --justdb cl-${NAME_DB}-devel
	rpm -e --justdb cl-${NAME_DB}-bench
	rpm -e --justdb cl-${NAME_DB}-server
	rpm -e --justdb cl-${NAME_DB}-shared
	rpm -e --justdb cl-${NAME_DB}-test
	rpm -e --justdb cl-${NAME_DB}-client
	rpm -e --justdb cl-mariadb-devel
	rpm -e --justdb cl-mariadb-bench
	rpm -e --justdb cl-mariadb-server
	rpm -e --justdb cl-mariadb-libs
	rpm -e --justdb cl-mariadb-test
	rpm -e --justdb cl-mariadb

fi
RELEASE_5=`cat /etc/redhat-release | grep "release 5"`
if [ -n "$RELEASE_5" ]; then
	CL_VER="cl5"
else
	CL_VER="cl6"
fi

if [ "$SQL_VERSION" == "auto" ]; then
	if [ "${MYSQL_OPT}" == "5.1" ]; then
		wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL_VER/cl-mysql-beta.repo
	        sed '/userstat/d' -i /etc/my.cnf
		sed '/userstat_running/d' -i /etc/my.cnf
	else
		wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL_VER/cl-mysql-beta-${MYSQL_OPT}.repo
	fi
fi
if [ "$SQL_VERSION" == "mysql50" ]; then
	wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL_VER/cl-mysql-beta-5.0.repo
fi
if [ "$SQL_VERSION" == "mysql51" ]; then
	wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL_VER/cl-mysql-beta.repo
        sed '/userstat/d' -i /etc/my.cnf
	sed '/userstat_running/d' -i /etc/my.cnf
fi
if [ "$SQL_VERSION" == "mysql55" ]; then
	wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL_VER/cl-mysql-beta-5.5.repo
fi
if [ "$SQL_VERSION" == "mariadb55" ]; then
	wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL_VER/cl-mariadb-5.5.repo
fi

#if [ "${MYSQL_OPT}" == "5.1" ]; then
#    if [ -n "$RELEASE_5" ]; then
#	wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/cl5/cl-mysql-beta.repo
#    else
#	wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/cl6/cl-mysql-beta.repo
#    fi
#    sed '/userstat/d' -i /etc/my.cnf
#    sed '/userstat_running/d' -i /etc/my.cnf
#
#else
#    if [ -n "$RELEASE_5" ]; then
#	wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/cl5/cl-mysql-beta-${MYSQL_OPT}.repo
#    else
#	wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/cl6/cl-mysql-beta-${MYSQL_OPT}.repo
#    fi
#fi
			
IS_MYSQL=`rpm -qa MySQL-server`
if [ -n "$IS_MYSQL" ]; then
	rpm -e --justdb MySQL-shared 
	rpm -e --justdb MySQL-server 
	rpm -e --justdb MySQL-devel 
	rpm -e --justdb MySQL-client 
	rpm -e --justdb MySQL-test
	rpm -e --justdb cpanel-MySQL-devel 
	rpm -e --justdb cpanel-MySQL-shared 
	rpm -e --justdb cpanel-MySQL-client 
	rpm -e --justdb cpanel-MySQL-server
	rpm -e --justdb cpanel-MySQL-test
	echo "Need to delete old mysql..."
fi
/sbin/service mysqld stop

if [ "$SQL_VERSION" == "auto" ]; then
    yum install cl-MySQL* -y
fi
if [ "$SQL_VERSION" == "mysql50" ]; then
    if [ -e /usr/libexec/mysqld ]; then
	mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
    fi
    yum install cl-MySQL-bench cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y
fi
if [ "$SQL_VERSION" == "mysql51" ]; then
    if [ -e /usr/libexec/mysqld ]; then
	mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
    fi
    yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y
fi
if [ "$SQL_VERSION" == "mysql55" ]; then
    if [ -e /usr/libexec/mysqld ]; then
	mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
    fi
    yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y
fi
if [ "$SQL_VERSION" == "mariadb55" ]; then
    yum install cl-mariadb cl-mariadb-bench cl-mariadb-devel cl-mariadb-libs cl-mariadb-server --nogpgcheck -y
fi

#/sbin/service mysqld stop
ln -sf /etc/init.d/mysqld.bkp /etc/init.d/mysqld

/sbin/service mysqld restart
echo "Giving mysqld a few seconds to start up...";
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
	/sbin/service db_governor restart
	echo "DB-Governor installed/updated...";
fi

echo "Installation mysql for db_governor completed"
echo "Rebuild php please... /usr/local/directadmin/custombuild/build php"
