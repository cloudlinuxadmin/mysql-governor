#!/bin/bash

mysqlTypeFileSet="/usr/share/lve/dbgovernor/mysql.type"

function checkFile(){
	if [ ! -e "$1" ]; then
		echo "Installtion error file ---$1---- does not exists"
		exit 1
	fi
}

function checkIfMySQL(){
	IS_MYSQL=`/bin/ps uax | /bin/grep mysqld | /bin/grep datadir`
	if [ -n "$IS_MYSQL" ]; then
	    echo "Stop hunging MySQL"
	    /usr/bin/killall -SIGTERM mysqld_safe
	    echo "Waiting for mysqld_safe stop"
	    sleep 10
	    /usr/bin/killall -SIGTERM mysqld
	    echo "Waiting for mysqld stop"
	    sleep 10
	fi
}

function installDb(){
	SQL_VERSION=$1
	
	CL=`echo -n "cl5"`
	CL6=`uname -a | grep "\.el6"`
	CL7=`uname -a | grep "\.el7"`
	if [ -n "$CL6" ]; then
	    CL=`echo -n "cl6"`
	    if [ -e /etc/my.cnf ]; then
        	sed '/userstat/d' -i /etc/my.cnf
	        sed '/userstat_running/d' -i /etc/my.cnf
	    fi
	fi
	if [ -n "$CL7" ]; then
	    CL=`echo -n "cl7"`
	    if [ -e /etc/my.cnf ]; then
        	sed '/userstat/d' -i /etc/my.cnf
	        sed '/userstat_running/d' -i /etc/my.cnf
	    fi
	fi
	yum clean all
	checkIfMySQL
	if [ "$SQL_VERSION" == "auto" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/mysql-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
          if [ -z "$CL7" ]; then
	  yum install mysql mysql-server mysql-libs mysql-devel mysql-bench  --nogpgcheck -y
          else
          yum install mariadb mariadb-server mariadb-libs mariadb-devel mariadb-bench  --nogpgcheck -y
          fi

	fi
	if [ "$SQL_VERSION" == "mysql50" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.0-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	    mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql51" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.1-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.5-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install libaio --nogpgcheck -y
	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel libaio --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql56" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.6-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install libaio --nogpgcheck -y
	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel libaio --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql57" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.7-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install libaio --nogpgcheck -y
	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel libaio --nogpgcheck -y
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mariadb55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mariadb-5.5-common.repo
	  yum install libaio --nogpgcheck -y
	  yum install cl-MariaDB-meta cl-MariaDB-meta-client cl-MariaDB-meta-devel libaio --nogpgcheck -y
	fi

	if [ "$SQL_VERSION" == "mariadb100" ]; then
	  rm -rf /usr/include/mysql
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mariadb-10.0-common.repo
	  yum install libaio --nogpgcheck -y
	  yum install cl-MariaDB-meta cl-MariaDB-meta-client cl-MariaDB-meta-devel libaio --nogpgcheck -y
	fi

	if [ "$SQL_VERSION" == "mariadb101" ]; then
	  rm -rf /usr/include/mysql
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mariadb-10.1-common.repo
	  yum install libaio --nogpgcheck -y
	  yum install cl-MariaDB-meta cl-MariaDB-meta-client cl-MariaDB-meta-devel libaio --nogpgcheck -y
	fi

	if [ ! -e /etc/my.cnf.bkp ]; then
	    cp -f /etc/my.cnf /etc/my.cnf.bkp
	fi
	sed /userstat/d -i /etc/my.cnf
	if [ -e /usr/lib/systemd/system/mysql.service ]; then
	    /bin/systemctl restart mysql.service
	else
	    /sbin/service mysql restart
	fi
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
	CL6=`uname -a | grep "\.el6"`
	CL7=`uname -a | grep "\.el7"`
	if [ -n "$CL6" ]; then
	    CL=`echo -n "cl6"`
	    if [ -e /etc/my.cnf ]; then
        	sed '/userstat/d' -i /etc/my.cnf
	        sed '/userstat_running/d' -i /etc/my.cnf
	    fi
	fi
	if [ -n "$CL7" ]; then
	    CL=`echo -n "cl7"`
	    if [ -e /etc/my.cnf ]; then
        	sed '/userstat/d' -i /etc/my.cnf
	        sed '/userstat_running/d' -i /etc/my.cnf
	    fi
	fi
    yum clean all
	if [ "$SQL_VERSION" == "auto" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/mysql-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install mysql mysql-server mysql-libs mysql-devel mysql-bench  --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	fi
	if [ "$SQL_VERSION" == "mysql50" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.0-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	    mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql51" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.1-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.5-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install libaio --nogpgcheck -y
	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel libaio --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql56" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.6-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install libaio --nogpgcheck -y
    	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel libaio --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mysql57" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mysql-5.7-common.repo
	  if [ -e /usr/libexec/mysqld ]; then
	   mv -f /usr/libexec/mysqld /usr/libexec/mysqld.bak
          fi
	  yum install libaio --nogpgcheck -y
    	  yum install cl-MySQL-meta cl-MySQL-meta-client cl-MySQL-meta-devel libaio --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	  ln -sf /etc/init.d/mysql /etc/init.d/mysqld
	fi
	if [ "$SQL_VERSION" == "mariadb55" ]; then
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mariadb-5.5-common.repo
	  yum install cl-MariaDB-meta cl-MariaDB-meta-client cl-MariaDB-meta-devel libaio --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	fi

	if [ "$SQL_VERSION" == "mariadb100" ]; then
	  rm -rf /usr/include/mysql
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mariadb-10.0-common.repo
	  yum install libaio --nogpgcheck -y
	  yum install cl-MariaDB-meta cl-MariaDB-meta-client cl-MariaDB-meta-devel libaio --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	fi

	if [ "$SQL_VERSION" == "mariadb101" ]; then
	  rm -rf /usr/include/mysql
	  wget -O /etc/yum.repos.d/cl-mysql.repo  http://repo.cloudlinux.com/other/$CL/mysqlmeta/cl-mariadb-10.1-common.repo
	  yum install libaio --nogpgcheck -y
	  yum install cl-MariaDB-meta cl-MariaDB-meta-client cl-MariaDB-meta-devel libaio --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	fi

	if [ ! -e /etc/my.cnf.bkp ]; then
	    cp -f /etc/my.cnf /etc/my.cnf.bkp
	fi
	sed /userstat/d -i /etc/my.cnf
	if [ -e /usr/lib/systemd/system/mysql.service ] || [ -e /etc/systemd/system/mysql.service ]; then
	    /bin/systemctl restart  mysql.service
	else
	    /sbin/service mysql restart
	fi
	echo "Giving mysqld a few seconds to start up...";
	sleep 10;
	

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
}



function installDbDevel(){
	SQL_VERSION=$1
	
        yum clean all
        if [ "$SQL_VERSION" == "mariadb101" ]; then
	  rm -rf /usr/include/mysql
	  yum reinstall cl-MariaDB101-devel --nogpgcheck -y
	fi
	if [ "$SQL_VERSION" == "mariadb100" ]; then
	  rm -rf /usr/include/mysql
	  yum reinstall cl-MariaDB100-devel --nogpgcheck -y
	fi

	echo "ReInstallation mysql-devel completed"
}

function installDbTestDevel(){
	SQL_VERSION=$1
	
	yum clean all
	if [ "$SQL_VERSION" == "mariadb101" ]; then
	  rm -rf /usr/include/mysql
	  yum reinstall cl-MariaDB101-devel --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	fi
	if [ "$SQL_VERSION" == "mariadb100" ]; then
	  rm -rf /usr/include/mysql
	  yum reinstall cl-MariaDB100-devel --nogpgcheck -y --enablerepo=cloudlinux-updates-testing
	fi

	echo "ReInstallation mysql-devel completed"
}
