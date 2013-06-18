Name: governor-mysql
Version: 1.0
Release: 7%{?dist}.cloudlinux
Summary: DB control utilities
License: CloudLinux Commercial License
URL: http://cloudlinux.com
Group: System Environment/Base
Source0: %{name}-%{version}.tar.bz2
Requires: glib2
Requires: ncurses
Requires: lve-utils >= 1.1-3
Requires: lve-stats >= 0.9-26
Requires: tmpwatch
Requires(preun): /sbin/chkconfig
BuildRequires: cmake
BuildRequires: ncurses-devel
BuildRequires: glib2-devel
BuildRequires: autoconf
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Conflicts: db-governor
Conflicts: db-governor-mysql
Conflicts: db_governor
Conflicts: cpanel-db-governor
%description
This package provides dbtop, db_governor utilities.

%prep

%setup -q

%build
cmake .
make
cd install
autoconf
%configure
make
cd -


%install
%{__rm} -rf $RPM_BUILD_ROOT

if [ -e autoconf ]; then                                                                                                                                                                                                                     
# Yuck. We're using autoconf 2.1x.                                                                                                                                                                                                           
  export PATH=.:$PATH                                                                                                                                                                                                                        
fi                                                                                                                                                                                                                                           

cd install                                                                                                                                                                                                                                             
make DESTDIR=$RPM_BUILD_ROOT install
cd -
mkdir -p $RPM_BUILD_ROOT/var/lve/dbgovernor/
mkdir -p $RPM_BUILD_ROOT/var/lve/dbgovernor-store/
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/
mkdir -p $RPM_BUILD_ROOT%{_sbindir}/
mkdir -p $RPM_BUILD_ROOT%{_libdir}/
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/container/
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/da
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/plesk
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/iworx
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/ispmanager
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/tmp
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/logs
mkdir -p $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/tmp
install -D -m 755 script/db_governor $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/
install -D -m 755 bin/db_governor $RPM_BUILD_ROOT%{_sbindir}/
install -D -m 755 bin/dbtop $RPM_BUILD_ROOT%{_sbindir}/
install -D -m 755 bin/mysql_unfreeze $RPM_BUILD_ROOT%{_sbindir}/
install -D -m 755 bin/dbctl $RPM_BUILD_ROOT%{_sbindir}/
install -D -m 600 db-governor.xml $RPM_BUILD_ROOT%{_sysconfdir}/container/mysql-governor.xml
install -D -m 755 lib/libgovernor.so $RPM_BUILD_ROOT%{_libdir}/
#install utility
install -D -m 755 install/cpanel/check_mysql_leave_pid.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/check_mysql_leave_pid.sh
install -D -m 755 install/cpanel/db_governor-clear-old-hook $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/db_governor-clear-old-hook
install -D -m 755 install/cpanel/install-db-governor $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/install-db-governor
install -D -m 755 install/cpanel/install-db-governor-beta $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/install-db-governor-beta
install -D -m 755 install/cpanel/cpanel-common-lve $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/cpanel-common-lve
install -D -m 755 install/cpanel/cpanel-delete-hooks $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/cpanel-delete-hooks
install -D -m 755 install/cpanel/cpanel-install-hooks $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/cpanel-install-hooks
install -D -m 755 install/cpanel/upgrade-mysql-disabler.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/upgrade-mysql-disabler.sh
install -D -m 755 install/da/install-db-governor.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/da/install-db-governor.sh
install -D -m 644 install/cpanel/cloudlinux.versions $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/cloudlinux.versions
install -D -m 755 install/cpanel/install-mysql-disabler.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/cpanel/install-mysql-disabler.sh
install -D -m 755 install/plesk/install-db-governor.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/plesk/install-db-governor.sh
install -D -m 755 install/iworx/install-db-governor.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/iworx/install-db-governor.sh
install -D -m 755 install/ispmanager/install-db-governor.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/ispmanager/install-db-governor.sh
install -D -m 755 install/other/install-db-governor.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/other/install-db-governor.sh
install -D -m 755 install/other/set_fs_suid_dumpable.sh $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/other/set_fs_suid_dumpable.sh

install -D -m 755 install/chk-mysqlclient $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/chk-mysqlclient
install -D -m 755 install/db-select-mysql $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/db-select-mysql
install -D -m 755 install/remove-mysqlclient $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/remove-mysqlclient
#install cron utility
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/cron.d/
install -D -m 644 cron/lvedbgovernor-utils-cron $RPM_BUILD_ROOT%{_sysconfdir}/cron.d/

touch $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/tmp/INFO                                                                                                                                                                                     
echo "CloudLinux" > $RPM_BUILD_ROOT/usr/share/lve/dbgovernor/tmp/INFO

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

%pre
/sbin/service db_governor stop > /dev/null 2>&1
rs=$(pgrep governor)
if [ ! -z "$rs" ];then
kill $(pgrep governor)
fi

%post
if [ $1 -gt 0 ] ; then
 if [ -e "/usr/share/lve/dbgovernor/other/set_fs_suid_dumpable.sh" ]; then
  /usr/share/lve/dbgovernor/other/set_fs_suid_dumpable.sh
 fi
fi
/sbin/chkconfig --add db_governor
/sbin/chkconfig --level 35 db_governor on

%preun
if [ $1 -eq 0 ]; then
    /sbin/service db_governor stop > /dev/null 2>&1
    /sbin/chkconfig --del db_governor
fi

%posttrans
/sbin/ldconfig
rm -rf /%{_libdir}/liblve.so.1
ln -s /%{_libdir}/liblve.so.0.9.0 /%{_libdir}/liblve.so.1


ldconfig
echo "Run script: /usr/share/lve/dbgovernor/mysqlgovernor.py --install"
echo "!!!Before making any changing with database make sure that you have reserve copy of users data!!!"
echo "Instruction: how to create whole database backup - http://docs.cloudlinux.com/index.html?backing_up_mysql.html"

%files
%defattr(-,root,root)
%doc LICENSE.TXT

%{_sbindir}/db_governor
%{_sbindir}/dbtop
%{_sbindir}/mysql_unfreeze
%{_sbindir}/dbctl
%{_libdir}/libgovernor.so
%config(noreplace) %{_sysconfdir}/container/mysql-governor.xml
%{_sysconfdir}/rc.d/init.d/*
/usr/share/lve/dbgovernor/*
%{_sysconfdir}/cron.d/lvedbgovernor-utils-cron
/var/lve/dbgovernor
/var/lve/dbgovernor-store
/usr/share/lve/dbgovernor/cpanel/logs
/usr/share/lve/dbgovernor/cpanel/tmp

%changelog
* Wed Jun 12 2013 Alexey Berezhok <alexey_com@ukr.net> 1.0-7
- Fixed dbctl unrestricted-all command
- Fixed dbctl restrict command
- Added symlink /etc/init.d/mysqld creation on /etc/init.d/mysql
- Added check type of mysql from file on mysqlclient install
- Added support of mariadb 5.5.30-17

* Tue Jun 11 2013 Alexey Berezhok <alexey_com@ukr.net> 1.0-6
- Fixed version MySQL for cPanel
- Added "Database backup" instruction

* Fri Jun 07 2013 Alexey Berezhok <alexey_com@ukr.net> 1.0-5
- Fixed db-update for Plesk

* Fri May 31 2013 Alexey Berezhok <alexey_com@ukr.net> 1.0-4
- Added db-update script
- Added al-php mysql update on database type changing
- Removed killuser mode in governor

* Mon May 20 2013 Pavel Shkatula <shpp@cloudlinux.com> 1.0-3
- Fixed dbctl list and big numbers issue

* Fri May 17 2013 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 1.0-2
- Fixed cPanel install script (changing from MariaDB to MySQL)

* Fri May 17 2013 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 1.0-1
- Added MariaDB instalation
- Added select MySQL server script

* Tue Apr 15 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-15
- Added set fs_suid_dumpable on package install or update

* Tue Apr 15 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-14
- Removed empty statistics saving to history (fix)

* Mon Apr 15 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-13
- Removed empty statistics saving to history

* Fri Apr 05 2013 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.9-12
- Added installation governor on non CL servers
- Removed lve requires
- Added MariaDB patch

* Mon Mar 18 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-11
- Fixed IO calculations

* Mon Mar 18 2013 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.9-10
- Fixed dbtop garbage
- Fixed cl-MySQL-server missed on install

* Fri Mar 15 2013 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.9-9
- Fixed dbtop last line error
- Fixed empty password error
- Fixed new lve-stats dependency

* Tue Mar 12 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-8
- Added mysql support 5.5.30, 5.1.68, 5.0.96, 5.1.67
- Fixed mysql crash (removed lve_exit)
- Fixed mysql hang up (added own trylock)
- Fixed rewrite config on the fly crash
- Fixed "PROCESSLIST" error for mysql 5.0

* Tue Feb 19 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-7
- Added postupcp hook for upgrade cPanel from 11.34 to 11.36

* Fri Feb 15 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-6
- Fixed bug in mysqldisabler script on cPanel (<11.36)

* Fri Feb 15 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-5
- Added installation on cPanel 11.36 (fix)

* Tue Feb 12 2013 Alexey Berezhok <alexey_com@ukr.net> 0.9-4
- Added installation on cPanel 11.36

* Thu Jan 24 2013 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.9-3
- Fixed header of dbctl list
- Show values less then 1Mb/s in dbctl list

* Fri Jan 18 2013 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.9-2
- Added logging queries on restrict
- Update MySQL vesrion 5.1.66, 5.5.28

* Mon Jan 14 2013 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.9-1
- Added new put in lve algorithm
- Added lve_enter_pid wrapper
- Added support of new MySQL with new algorithm of work (cPanel 5.5, 5.1, 5.0 and standart CL5 & CL6 mysql 5.0 and 5.1)

* Mon Dec 10 2012 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.8-40
- Fixed dbctl negative read/write limits

* Wed Dec 05 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-39
- Added lve-stats 0.9-13 require

* Tue Dec 04 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-38
- Changed max_sim_connections to average_connections

* Mon Dec 03 2012 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.8-37
- Added /vr/lve/dbgovernor directory creation

* Fri Nov 30 2012 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.8-36
- Added CAUSE history field saving
- Enabled statistics by default
- Disabled killuser by default
- Disabled mysql-debuginfo installation(for cPanel)
- Enabled force mysql installation(for cPanel)
- Fixed segfault in dbctl
- Fixed trouble with g_hash_table_remove_all

* Mon Nov 26 2012 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.8-35
- Added statistics collection(lve-stats part)

* Wed Nov 21 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-34
- Fixed error on mysql 5.5 installtion on i386 

* Wed Nov 21 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-33
- Change mysql-governor.xml access mask to 600

* Tue Nov 19 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-32
- Rename "watch" command to "monitor"

* Mon Nov 19 2012 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.8-31
- Added statistics collection(governor part)
- Added restore screen and exit on CTRL-C - dbtop
- Added coredump creation on governor crash
- Added directory for future statistics storage

* Mon Nov 14 2012 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.8-30
- Added unresrict user on ignore
- Added dbctl watch command for disable ignoring
- Fixed level format error

* Mon Nov 12 2012 Alexey Berezhok <alexey_com@ukr.net>, Pavel Shkatula <shpp@cloudlinux.com> 0.8-29
- Added dbctl utility
- Added dbtop -c mode
- Added dbtop crash dump tracing
- Added killuser config flag 

* Thu Nov 01 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-28
- Fixed is_in_lve in mysql

* Tue Oct 30 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-27
- Added check cpu, read, write before adding to counter

* Mon Oct 29 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-26
- Fixed governors resource usage calculation(end of request)

* Mon Oct 29 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-25
- Fixed governors resource usage calculation

* Fri Oct 26 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-24
- Fixed governors statistics calculation
- Show user load even when user is restricted
- Fixed dbtop header

* Thu Oct 25 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-23
- Added support fixed MySQL (5.5.27, 5.0.95, 5.1.61, 5.0.92, 5.1.63)

* Fri Oct 19 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-22
- Added support MySQL (5.5.27, 5.0.95, 5.1.61, 5.0.92)
- Fixed "Unrecognized option" under CL5

* Thu Oct 11 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-21
- Added new MySQL installation (5.1.63-14)

* Mon Oct 08 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-20
- Added new MySQL installation (5.1.63-12)

* Mon Oct 08 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-19
- Error on Inside LVE

* Mon Oct 04 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-18
- Change liblve.so to liblve.so.0

* Mon Oct 04 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-17
- Added new MySQL installation(5.1.63-11)

* Mon Oct 03 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-16
- Decreased mutex lock on info send(to daemon)
- Added new MySQL installation(5.1.63-10)

* Mon Oct 01 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-15
- Added new MySQL installation(5.1.63-9)

* Thu Sep 27 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-14
- Decreased time of lock in MySQL

* Wed Sep 26 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-13
- Removed kill_connection on unrestrict
- Changed mysql+LVE algorithm

* Mon Sep 24 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-12
- Added kill_connection on unrestrict

* Mon Sep 24 2012 Alexey Berezhok <alexey_com@ukr.net>,  Pavel Shkatula <shpp@cloudlinux.com> 0.8-11
- Changed algorithm of thread locking (MySQL part)
- Fixed error with lost TID cleaning
- Added userstat cleaning for MySQL 5.1
- Added mysql stoping before installation for MySQL 5.5

* Wed Sep 17 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-10
- Fixed error in install script

* Mon Sep 17 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-9
- Move calculation to separate thread
- Close semaphore on error
- Added limiting connection per user on restrict

* Fri Sep 14 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-8
- Fixed bug in LVE setting creation(on install)

* Thu Sep 13 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-7
- Optimization of work
- Added LVE support
- Added two mode of unrestrict mode for mysql_unfreeze (old and new), added option - help
- Added new mysql 5.1, 5.0, 5.5 support (with LVE patches)
- Added new mode of dbtop sorting (by time to end restrict, and by restrict level)
- Changed dafault config limits
- Added usage save-all-parameters on VE container creation

* Fri Sep 07 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-6
- Fixed error in DA, Plesk installation processes

* Thu Sep 06 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-5
- Added MySQL 5.5 support
- Added support of ISPManager, Plesk, IWorx
- Renamed install-mysql.py to mysqlgovernor.py

* Tue Sep 04 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-4
- Fixed bug in DA installator
- Fixed segfault bug on i686 arch

* Fri Aug 31 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-3
- Fixed memory leak
- Optimized algorithm of TID saving
- Added support 5.0 mysql for cPanel
- Fixed calculation of Resource Usage once a second
- Added commands clean-mysql and clean-mysql-delete
- Added DA mysql (5.1 and 5.0) support

* Thu Aug 23 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-2
- Fixed mysql - governor deadlock
- Changed output format of dbtop
- Changed default limits for cpu and periods

* Fri Aug 17 2012 Alexey Berezhok <alexey_com@ukr.net> 0.8-1
- Changed package name
- Changed analytic algorithm
- Added library for mysql extension
- Changed configuration list
- Removed mysql_connector

* Tue Jul 31 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-11
- Fixed freeze connector on users refresh
- Increased CHECKTICKS detalization

* Tue Jul 25 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-10
- Fixed error with freeze governor
- Fixed error with hang up threads of dbtop
- Disable --install-beta

* Tue Jul 24 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-8
- Added debuginfo

* Thu Jul 19 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-7
- Added support MySQL 5.1.63-2

* Thu Jun 27 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-6
- Fixed bug with mysql 5.5 detection. Added beta mysql installation

* Thu Jun 21 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-5
- Restore workin of old-hook utility for cPanel broken in 0.7-1 version

* Thu Jun 21 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-4
- Added information on installation. Added governor restarting on cpanel utility

* Thu Jun 21 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-3
- Fixed package distributive name

* Thu Jun 21 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-2
- Fixed dependency bug in package

* Tue Jun 19 2012 Alexey Berezhok <alexey_com@ukr.net> 0.7-1
- Added mysql install utility for cPanel, DA, Plesk, iWorx, ISPManager

* Tue Jun 12 2012 Alexey Berezhok <alexey_com@ukr.net> 0.6-5
- Fixed bug with mutex locking in connector
- Reorganized procedure of information exchange between governor and connector
- Fixed test mode
- Fixed bug in restriction algorithm

* Mon May 14 2012 Alexey Berezhok <alexey_com@ukr.net> 0.6-4
- Fixed bug with no limiting in i386 arch

* Fri Nov 04 2011 Alexey Berezhok <alexey_com@ukr.net> 0.6-2
- Fix in spec

* Tue Oct 04 2011 Alexey Berezhok <alexey_com@ukr.net> 0.6-1
- Added triggers for restrict and slow query
- Added debug info mode for slow query
- Added connection checking

* Tue Sep 06 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-10
- Added mysql 5.5 support

* Fri Aug 26 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-9
- Fixed mysql identification

* Thu Aug 11 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-8
- Segfault mysql_connector fixed

* Thu Aug 04 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-7
- Minor fixes
- Added mysql real users list caching
- Added user refresh interval into config file(default 5 minutes)

* Tue Jul 19 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-6
- Added SHOW PROCESSLIST info into restrict log

* Mon Jul 18 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-5
- Fixed error with query info output into restrict log

* Wed Jul 13 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-4
- Added check from selfblocking mysql user
- Review service script

* Thu Jul 07 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-3
- Change path to logs and socket, added loadavg info into training log

* Wed Jul 06 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-2
- Added attribute format for restrict log

* Tue Jul 05 2011 Alexey Berezhok <alexey_com@ukr.net> 0.5-1
- Added separate training log
- Changed request to DB (without temporary tables)
- Another small fixes

* Thu Jun 23 2011 Alexey Berezhok <alexey_com@ukr.net> 0.4-7
- Change restrict log format

* Wed Jun 22 2011 Alexey Berezhok <alexey_com@ukr.net> 0.4-6
- Up all default limits in config file

* Thu Jun 16 2011 Alexey Berezhok <alexey_com@ukr.net> 0.4-5
- Fix error in pre hook

* Thu Jun 16 2011 Alexey Berezhok <alexey_com@ukr.net> 0.4-4
- Fix eroor in dependencies

* Thu Jun 16 2011 Alexey Berezhok <alexey_com@ukr.net> 0.4-3
- Remove training info from restrict log to error

* Wed Jun 15 2011 Alexey Berezhok <alexey_com@ukr.net> 0.4-2
- Add auto stop and auto kill db-governors processes on update

* Fri Jun 10 2011 Alexey Berezhok <alexey_com@ukr.net> 0.4-1
- New functionality

* Thu Mar 24 2011 Alexey Berezhok <alexey_com@ukr.net> 0.3-11
- Changed strncpy to strlcpy
- Added debugmode

* Wed Mar 23 2011 Alexey Berezhok <alexey_com@ukr.net> 0.3-10
- Removed strange users form dbtop
- Added log for restriction event

* Thu Feb 24 2011 Alexey Berezhok <alexey_com@ukr.net> 0.3-9
- Change mysql-governor.xml. Remove connected_time.

* Tue Feb 22 2011 Alexey Berezhok <alexey_com@ukr.net> 0.3-8
- Fix cpu_time freezing
- Removed timer from connector that freeze governor statistic

* Thu Dec 06 2010 Alexey Berezhok <alexey_com@ukr.net> 0.3-7
- Add sorting by username
- Fix bug with newline when terminal resized

* Thu Dec 03 2010 Alexey Berezhok <alexey_com@ukr.net> 0.3-6
- Fixed bug with one info string under i386 system

* Thu Dec 02 2010 Alexey Berezhok <alexey_com@ukr.net> 0.3-5
- Change NaN to Ovf. Remove color scheme for usually item string

* Tue Nov 19 2010 Alexey Berezhok <alexey_com@ukr.net> 0.3-4
- Add toggle color mode and two-color mode by one key. Remove command help and colorize

* Tue Nov 17 2010 Alexey Berezhok <alexey_com@ukr.net> 0.3-3
- Add color mode for dbtop, add output all parameters(1,2,3,4 - screens), Ctrl+C - exit, merge CAUSE and TIMEOUT field

* Tue Nov 16 2010 Alexey Berezhok <alexey_com@ukr.net> 0.3-2
- Add dbtop-help, view sorted column, add cause of restrict, add correct view after resizing

* Fri Nov 12 2010 Alexey Berezhok <alexey_com@ukr.net> 0.3-1
- Add new dbtop view and sort, add suport mysql command KILL CONNECTION|QUERY 'user_name', add check mysql version

* Thu Nov 04 2010 Alexey Berezhok <alexey_com@ukr.net> 0.2-1                                                                                                
- db_governor opens two db connections: for reading, for sending command

* Mon Nov 01 2010 Alexey Berezhok <alexey_com@ukr.net> 0.2-0.1
- Add dynamic loading mysql client's library

* Thu Oct 27 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.4
- Add detail log info. Add analyzing testmode parameter (report interval). Output max values info into log file in test mode

* Mon Sep 27 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.4
- Add notification on zero default limit

* Mon Sep 20 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.4
- Add reading timeout from cfg. dbtop crashed when terminal resized, dbtop displayed number in format -0.000

* Fri Sep 16 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.4
- Remove README from /var/log/db_governor

* Fri Sep 15 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.4
- Add client section analizing in ~/.my.cnf

* Fri Sep 14 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.4
- Add client section analizing in my.cnf

* Fri Sep 13 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.4
- Killconnection was divided on killconnection and killquery

* Fri Aug 27 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.4
- Package is divided into two parts connector and manager

* Thu Aug 26 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.3
- Add c-parameter - kill connections type

* Thu Jul 09 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.2
- New init.d script. Add test statistics.

* Thu Jun 21 2010 Alexey Berezhok <alexey_com@ukr.net> 0.1-0.1
- Initial Package
