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
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install mysql mysql-server mysql-bench mysql-shared mysql-libs --nogpgcheck -y
	fi
	if [ "$SQL_VERSION" == "mysql50" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-5.0-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	    mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-bench cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql51" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-5.1-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-5.5-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared libaio --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql56" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-5.6-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared libaio --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mariadb55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mariadb-5.5-common.repo
	  yum install cl-mariadb cl-mariadb-bench cl-mariadb-devel cl-mariadb-libs cl-mariadb-server libaio --nogpgcheck -y
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

function installDbTest(){
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
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install mysql mysql-server mysql-bench mysql-shared mysql-libs --nogpgcheck -y --enablerepo=cl-mysql-testing
	fi
	if [ "$SQL_VERSION" == "mysql50" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-5.0-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	    mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-bench cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y --enablerepo=cl-mysql-5.0-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql51" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-5.1-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared --nogpgcheck -y --enablerepo=cl-mysql-5.1-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-5.5-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared libaio --nogpgcheck -y --enablerepo=cl-mysql-5.5-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql56" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mysql-5.6-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-client cl-MySQL-devel cl-MySQL-server cl-MySQL-shared libaio --nogpgcheck -y --enablerepo=cl-mysql-5.6-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mariadb55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqls/cl-mariadb-5.5-common.repo
	  yum install cl-mariadb cl-mariadb-bench cl-mariadb-devel cl-mariadb-libs cl-mariadb-server libaio --nogpgcheck -y --enablerepo=cl-mariadb-5.5-testing
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