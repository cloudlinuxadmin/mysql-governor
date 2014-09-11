# Copyright 2000-2008 MySQL AB, 2008 Sun Microsystems, Inc.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING. If not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston
# MA  02110-1301  USA.

%define mysql_version		5.1.73

# NOTE: "vendor" is used in upgrade/downgrade check, so you can't
# change these, has to be exactly as is.
%define mysql_old_vendor	MySQL AB
%define mysql_vendor		Sun Microsystems, Inc.

%define release 14%{?dist}.cloudlinux
%define mysql_license	GPL
%define mysqld_user	mysql
%define mysqld_group	mysql
%define server_suffix -standard
%define mysqldatadir /var/lib/mysql

# all unpackaged files removed
#%define _unpackaged_files_terminate_build 0

%define see_base For a description of MySQL see the base MySQL RPM or http://www.mysql.com

# On SuSE 9 no separate "debuginfo" package is built. To enable basic
# debugging on that platform, we don't strip binaries on SuSE 9. We
# disable the strip of binaries by redefining the RPM macro
# "__os_install_post" leaving out the script calls that normally does
# this. We do this in all cases, as on platforms where "debuginfo" is
# created, a script "find-debuginfo.sh" will be called that will do
# the strip anyway, part of separating the executable and debug
# information into separate files put into separate packages.
#
# Some references (shows more advanced conditional usage):
# http://www.redhat.com/archives/rpm-list/2001-November/msg00257.html
# http://www.redhat.com/archives/rpm-list/2003-February/msg00275.html
# http://www.redhat.com/archives/rhl-devel-list/2004-January/msg01546.html
# http://lists.opensuse.org/archive/opensuse-commit/2006-May/1171.html

%define __os_install_post /usr/lib/rpm/brp-compress

Name:       cl-MySQL51
Summary:	MySQL - a very fast and reliable SQL database server
Group:		Applications/Databases
Version:	%{mysql_version}
Release:	%{release}
License:	Copyright 2000-2008 MySQL AB, 2009 Sun Microsystems, Inc.  All rights reserved.  Use is subject to license terms.  Under %{mysql_license} license as shown in the Description field.
Source:		http://www.mysql.com/Downloads/MySQL-5.1/mysql-%{mysql_version}.tar.gz

Patch1:     0001-pointer-patch-centos-4.patch
#Patch2:     0002-Cloud-Linux-userstat_mysql.patch
Patch3:     max_connection2_mysql_5_1_73_b410.patch
#Patch4:     0004-cpanel-perl.patch
#Patch5:     0005-autogen.patch
Patch6:     mysql-test__db_test.1.patch

URL:		http://www.mysql.com/
Packager:	Sun Microsystems, Inc. Product Engineering Team <build@mysql.com>
Vendor:		%{mysql_vendor}
BuildRequires: ncurses-devel bison
AutoReq:       0
Autoprov: 0

# Think about what you use here since the first step is to
# run a rm -rf
BuildRoot:    %{_tmppath}/%{name}-%{version}-build

# From the manual
%description
The MySQL(TM) software delivers a very fast, multi-threaded, multi-user,
and robust SQL (Structured Query Language) database server. MySQL Server
is intended for mission-critical, heavy-load production systems as well
as for embedding into mass-deployed software. MySQL is a trademark of
Sun Microsystems, Inc.

Copyright 2000-2008 MySQL AB, 2009 Sun Microsystems, Inc.  All rights reserved.
Use is subject to license terms.

This software comes with ABSOLUTELY NO WARRANTY. This is free software,
and you are welcome to modify and redistribute it under the GPL license.

The MySQL web site (http://www.mysql.com/) provides the latest
news and information about the MySQL software. Also please see the
documentation and the manual for more information.

%package server
Summary:	MySQL - a very fast and reliable SQL database server
Group:		Applications/Databases
Requires: coreutils grep procps /usr/sbin/useradd /usr/sbin/groupadd /sbin/chkconfig
# Needed to give access to mysql client for %post calls.
Requires(post): %{name}-client
Requires: %{name}-client
AutoReq:       0
Autoprov: 0

%description server
The MySQL(TM) software delivers a very fast, multi-threaded, multi-user,
and robust SQL (Structured Query Language) database server. MySQL Server
is intended for mission-critical, heavy-load production systems as well
as for embedding into mass-deployed software. MySQL is a trademark of
Sun Microsystems, Inc.

Copyright 2000-2008 MySQL AB, 2009 Sun Microsystems, Inc.  All rights reserved.
Use is subject to license terms.

This software comes with ABSOLUTELY NO WARRANTY. This is free software,
and you are welcome to modify and redistribute it under the GPL license.

The MySQL web site (http://www.mysql.com/) provides the latest
news and information about the MySQL software. Also please see the
documentation and the manual for more information.

This package includes the MySQL server binary (incl. InnoDB) as well
as related utilities to run and administrate a MySQL server.

If you want to access and work with the database, you have to install
package "MySQL-client" as well!

%package client
Summary: MySQL - Client
Group: Applications/Databases
AutoReq:       0
Autoprov: 0

%description client
This package contains the standard MySQL clients and administration tools. 

%{see_base}

%package test
Summary: MySQL - Test suite
Group: Applications/Databases
AutoReqProv: no
AutoReq:       0
Autoprov: 0

%description test
This package contains the MySQL regression test suite.

%{see_base}

%package devel
Summary: MySQL - Development header files and libraries
Group: Applications/Databases
AutoReq:       0
Autoprov: 0

%description devel
This package contains the development header files and libraries
necessary to develop MySQL client applications.

%{see_base}

%package shared
Summary: MySQL - Shared libraries
Group: Applications/Databases
AutoReq:       0
Autoprov: 0

%description shared
This package contains the shared libraries (*.so*) which certain
languages and applications need to dynamically load and use MySQL.

%package -n cl-MySQL-meta
Summary: MySQL meta package
Group: Applications/Databases
Requires: cl-MySQL-meta-client
Requires: %{name}-server
Requires: %{name}-shared
Provides:  msqlormysql mysql-server mysql-libs mysql MySQL MySQL-server
Provides:  mysql-bench MySQL-bench mysql-test MySQL-test
Provides:  mysql-shared MySQL-shared
Obsoletes: mysql-libs
AutoReq: 0
%ifarch %{ix86}
Provides: libtool(/usr/lib/mysql/libmysqlclient.la)
Provides: libtool(/usr/lib/mysql/libmysqlclient_r.la)
Provides: libtool(/usr/lib/mysql/libz.la)
Provides: libtool(/usr/lib/mysql/plugin/ha_example.la)
Provides: libtool(/usr/lib/mysql/plugin/ha_innodb_plugin.la)
Provides: libmysqlclient.so.16
Provides: libmysqlclient.so.16(libmysqlclient_16)
Provides: libmysqlclient_r.so.16
Provides: libmysqlclient_r.so.16(libmysqlclient_16)
%else
Provides: libtool(/usr/lib64/mysql/libmysqlclient.la)
Provides: libtool(/usr/lib64/mysql/libmysqlclient_r.la)
Provides: libtool(/usr/lib64/mysql/libz.la)
Provides: libtool(/usr/lib64/mysql/plugin/ha_example.la)
Provides: libtool(/usr/lib64/mysql/plugin/ha_innodb_plugin.la)
Provides: libmysqlclient.so.16()(64bit)
Provides: libmysqlclient.so.16(libmysqlclient_16)(64bit)
Provides: libmysqlclient_r.so.16()(64bit)
Provides: libmysqlclient_r.so.16(libmysqlclient_16)(64bit)
%endif


%description -n cl-MySQL-meta
MySql-server meta package.

%package -n cl-MySQL-meta-client
Summary: MySQL - Client meta package
Group: Applications/Databases
Requires: %{name}-client
Provides: mysql-client MySQL-client
AutoReq: 0

%description -n cl-MySQL-meta-client
MySql-client meta package.

%package -n cl-MySQL-meta-devel
Summary: MySQL - Development header files and libraries meta package
Group: Applications/Databases
Requires: %{name}-devel
Provides: mysql-devel MySQL-devel
AutoReq: 0

%description -n cl-MySQL-meta-devel
MySql-devel meta package.

%prep
%define _default_patch_fuzz 0

# We unpack the source two times, for 'debug' and 'release' build.
%setup -q -T -a 0 -c -n mysql-%{mysql_version}
mv mysql-%{mysql_version} mysql-debug-%{mysql_version}
cd mysql-debug-%{mysql_version}
%patch1 -p3
#%patch2 -p3
%patch3 -p1
#%patch4 -p3
#%patch5 -p3
%patch6 -p2

find . -exec touch -r Makefile.in '{}' ';'
rm -f sql/sql_yacc.cc sql/sql_yacc.h
cd ..

%setup -q -D -T -a 0 -n mysql-%{mysql_version}
mv mysql-%{mysql_version} mysql-release-%{mysql_version}
cd mysql-release-%{mysql_version}
%patch1 -p3
#%patch2 -p3
%patch3 -p1
#%patch4 -p3
#%patch5 -p3
%patch6 -p2

find . -exec touch -r Makefile.in '{}' ';'
rm -f sql/sql_yacc.cc sql/sql_yacc.h
cd ..

%build

export MAKE_JFLAG=${MYSQL_BUILD_MAKE_JFLAG:-}

# GCC 2.96 is failing on mandrake 8.2 because it's using -O3 and crashing the compiler. 
# We think this is a 2.96 bug so we're forcing -O2 on all 2.96 compilers
# Redhat 9 is compiling for some reason...
%define is_gcc296 %(gcc --version 2>&1|grep -c "2\.96")
%if %is_gcc296
 RPM_OPT_FLAGS="$RPM_OPT_FLAGS -O2"
 export RPM_OPT_FLAGS
 echo gcc 2.96 detected. Lowering optimization to -O2
%endif

# Use our own copy of glibc

OTHER_LIBC_DIR=/usr/local/mysql-glibc
USE_OTHER_LIBC_DIR=""
if test -d "$OTHER_LIBC_DIR"
then
  USE_OTHER_LIBC_DIR="--with-other-libc=$OTHER_LIBC_DIR"
fi

# Use the build root for temporary storage of the shared libraries.

RBR=$RPM_BUILD_ROOT

# Clean up the BuildRoot first
[ "$RBR" != "/" ] && [ -d $RBR ] && rm -rf $RBR;
mkdir -p $RBR%{_libdir}/mysql

#
# Use MYSQL_BUILD_PATH so that we can use a dedicated version of gcc
#
PATH=${MYSQL_BUILD_PATH:-/bin:/usr/bin}
export PATH

# Build the Debug binary.

CC="gcc"
CXX="gcc"
export CC CXX

# Prepare compiler flags

##############################################################################
#
#  Build the debug version
#
##############################################################################
CFLAGS="$RPM_OPT_FLAGS"
CXXFLAGS="$RPM_OPT_FLAGS -felide-constructors -fno-exceptions -fno-rtti -Wno-unused-parameter"
CFLAGS=`echo   " $CFLAGS "   | \
    sed -e 's/-O[0-9]*\b/ /g' -e 's/ -unroll2 / /' -e 's/ -ip / /' \
        -e 's/^ //' -e 's/ $//'`
CXXFLAGS=`echo " $CXXFLAGS " | \
    sed -e 's/-O[0-9]*\b/ /g' -e 's/ -unroll2 / /' -e 's/ -ip / /' \
        -e 's/^ //' -e 's/ $//'`
export CFLAGS CXXFLAGS

cd mysql-debug-%{mysql_version}
./configure \
    --with-mysqld-ldflags='-static' \
    --with-client-ldflags='-static' \
    --with-mysqld-libs=-lrt \
    --with-zlib-dir=bundled \
    --enable-assembler \
    --enable-local-infile \
    --with-fast-mutexes \
    --with-mysqld-user=%{mysqld_user} \
    --with-unix-socket-path=/var/lib/mysql/mysql.sock \
    --with-pic \
    --prefix=/ \
    --with-extra-charsets=all \
    --with-ssl \
    --exec-prefix=%{_exec_prefix} \
    --libexecdir=%{_sbindir} \
    --libdir=%{_libdir} \
    --sysconfdir=%{_sysconfdir} \
    --datadir=%{_datadir} \
    --localstatedir=%{mysqldatadir} \
    --infodir=%{_infodir} \
    --includedir=%{_includedir} \
    --mandir=%{_mandir} \
    --enable-thread-safe-client \
    --with-readline \
    --with-big-tables \
    --with-innodb \
	--with-archive-storage-engine \
	--with-csv-storage-engine \
	--with-blackhole-storage-engine \
	--with-federated-storage-engine \
	--with-partition \
    --without-plugin-daemon_example \
    --without-plugin-ftexample \
    --without-plugin-ndbcluster \
    --enable-shared \
		--with-debug \
		--without-mysqlmanager \
		--without-docs \
		--without-man \
		--with-comment="MySQL Community Server - Debug (%{mysql_license})"
# Do a make separatley so rpm can detect a make failure.
make -j10 ${MAKE_JFLAG}

##############################################################################
#
#  Build the release binary
#
##############################################################################

cd ../mysql-release-%{mysql_version}
CFLAGS="$RPM_OPT_FLAGS"
CXXFLAGS="$RPM_OPT_FLAGS -felide-constructors -fno-exceptions -fno-rtti"
export CFLAGS CXXFLAGS
./configure \
    --with-mysqld-ldflags='-static' \
    --with-client-ldflags='-static' \
    --with-mysqld-libs=-lrt \
    --with-zlib-dir=bundled \
    --enable-assembler \
    --enable-local-infile \
    --with-fast-mutexes \
    --with-mysqld-user=%{mysqld_user} \
    --with-unix-socket-path=/var/lib/mysql/mysql.sock \
    --with-pic \
    --prefix=/ \
    --with-extra-charsets=all \
    --with-ssl \
    --exec-prefix=%{_exec_prefix} \
    --libexecdir=%{_sbindir} \
    --libdir=%{_libdir} \
    --sysconfdir=%{_sysconfdir} \
    --datadir=%{_datadir} \
    --localstatedir=%{mysqldatadir} \
    --infodir=%{_infodir} \
    --includedir=%{_includedir} \
    --mandir=%{_mandir} \
    --enable-thread-safe-client \
    --with-readline \
    --with-big-tables \
    --with-innodb \
	--with-archive-storage-engine \
	--with-csv-storage-engine \
	--with-blackhole-storage-engine \
	--with-federated-storage-engine \
	--with-partition \
    --without-plugin-daemon_example \
    --without-plugin-ftexample \
    --without-plugin-ndbcluster \
    --enable-shared \
		--with-comment="MySQL Community Server (%{mysql_license})"
# Do a make separatley so rpm can detect a make failure.
make -j10 ${MAKE_JFLAG}

%install
RBR=$RPM_BUILD_ROOT
MBD=$RPM_BUILD_DIR/mysql-%{mysql_version}/mysql-release-%{mysql_version}

# Clean up the BuildRoot first - Fedora is doing this now and it's correct procedure...
[ "$RBR" != "/" ] && [ -d $RBR ] && rm -rf $RBR;

# Ensure that needed directories exists
install -d $RBR%{_sysconfdir}/{logrotate.d,init.d}
install -d $RBR%{mysqldatadir}/mysql
install -d $RBR%{_datadir}/mysql-test
install -d $RBR%{_includedir}
install -d $RBR%{_libdir}/mysql
install -d $RBR%{_mandir}
install -d $RBR%{_sbindir}

# Include libgcc.a in the devel subpackage (BUG 4921)
CC="${CC:-gcc}" 
if expr "$CC" : ".*gcc.*" > /dev/null ;
then
  libgcc=`$CC $CFLAGS --print-libgcc-file`
  if [ -f $libgcc ]
  then
    %define have_libgcc 1
    install -m 644 $libgcc $RBR%{_libdir}/mysql/libmygcc.a
  fi
fi

# Install all binaries 
(cd $MBD && make install DESTDIR=$RBR testroot=%{_datadir})
# Old packages put shared libs in %{_libdir}/ (not %{_libdir}/mysql), so do
# the same here.
mv $RBR/%{_libdir}/mysql/*.so* $RBR/%{_libdir}/

# install "mysqld-debug"
$MBD/libtool --mode=execute install -m 755 \
                 $RPM_BUILD_DIR/mysql-%{mysql_version}/mysql-debug-%{mysql_version}/sql/mysqld \
                 $RBR%{_sbindir}/mysqld-debug

# install saved perror binary with NDB support (BUG#13740)
install -m 755 $MBD/extra/perror $RBR%{_bindir}/perror

# Install logrotate and autostart
install -m 644 $MBD/support-files/mysql-log-rotate $RBR%{_sysconfdir}/logrotate.d/mysql
install -m 755 $MBD/support-files/mysql.server $RBR%{_sysconfdir}/init.d/mysql

# in RPMs, it is unlikely that anybody should use "sql-bench"
rm -rf $RBR%{_datadir}/sql-bench

# Some SQL-bench files going to / ???
rm -rf $RBR/sql-bench


# Create a symlink "rcmysql", pointing to the init.script. SuSE users
# will appreciate that, as all services usually offer this.
ln -s %{_sysconfdir}/init.d/mysql $RPM_BUILD_ROOT%{_sbindir}/rcmysql

# Touch the place where the my.cnf config file and mysqlmanager.passwd
# (MySQL Instance Manager password file) might be located
# Just to make sure it's in the file list and marked as a config file
touch $RBR%{_sysconfdir}/my.cnf
touch $RBR%{_sysconfdir}/mysqlmanager.passwd

# Prevent autodeps parsing of perl scripts that ship with MySQL-server and MySQL-client
chmod 644 $RBR/usr/bin/mysql_convert_table_format $RBR/usr/bin/mysql_fix_extensions $RBR/usr/bin/mysql_setpermission $RBR/usr/bin/mysql_zap $RBR/usr/bin/mysqld_multi $RBR/usr/bin/mysqldumpslow $RBR/usr/bin/mysqlhotcopy
chmod 644 $RBR/usr/bin/mysql_find_rows $RBR/usr/bin/mysqlaccess

%ifarch %{ix86}
cat $RBR%{_bindir}/mysql_config | sed "s/pkglibdir='\/usr\/lib\/mysql'/pkglibdir='\/usr\/lib'/g" > $RBR%{_bindir}/mysql_config.tmp
%else
cat $RBR%{_bindir}/mysql_config | sed "s/pkglibdir='\/usr\/lib64\/mysql'/pkglibdir='\/usr\/lib64'/g" > $RBR%{_bindir}/mysql_config.tmp
%endif
mv -f $RBR%{_bindir}/mysql_config.tmp $RBR%{_bindir}/mysql_config
chmod 755 $RBR%{_bindir}/mysql_config


%pre server

# Shut down a previously installed server first
/sbin/service mysql stop || /bin/true
sleep 5

%triggerpostun -n %{name}-server -- MySQL-server
# Work around mysqld being stopped when MySQL-server which we replace gets uninstalled.
/sbin/service mysql start || /bin/true

%post server
mysql_datadir=%{mysqldatadir}

# Create data directory if needed
if test ! -d $mysql_datadir; then mkdir -m 755 $mysql_datadir; fi
if test ! -d $mysql_datadir/mysql; then mkdir $mysql_datadir/mysql; fi
if test ! -d $mysql_datadir/test; then mkdir $mysql_datadir/test; fi

# Make MySQL start/shutdown automatically when the machine does it.
/sbin/chkconfig --add mysql

# Create a MySQL user and group. Do not report any problems if it already
# exists.
groupadd -r %{mysqld_group} 2> /dev/null || true
useradd -M -r -d $mysql_datadir -s /bin/bash -c "MySQL server" -g %{mysqld_group} %{mysqld_user} 2> /dev/null || true 
# The user may already exist, make sure it has the proper group nevertheless (BUG#12823)
usermod -g %{mysqld_group} %{mysqld_user} 2> /dev/null || true

# Change permissions so that the user that will run the MySQL daemon
# owns all database files.
chown -R %{mysqld_user}:%{mysqld_group} $mysql_datadir

# Initiate databases if needed
%{_bindir}/mysql_install_db --rpm --user=%{mysqld_user}

# Upgrade databases if needed would go here - but it cannot be automated yet

# Change permissions again to fix any new files.
chown -R %{mysqld_user}:%{mysqld_group} $mysql_datadir

# Fix permissions for the permission database so that only the user
# can read them.
chmod -R og-rw $mysql_datadir/mysql

# Stop the service prior to running build_mysql_conf
/sbin/service mysql stop

# Allow mysqld_safe to start mysqld and print a message before we exit
sleep 2

#echo "Thank you for installing the MySQL Community Server! For Production
#systems, we recommend MySQL Enterprise, which contains enterprise-ready
#software, intelligent advisory services, and full production support with
#scheduled service packs and more.  Visit www.mysql.com/enterprise for more
#information." 

if [ -x '/usr/local/cpanel/bin/build_mysql_conf' ]; then
  /usr/local/cpanel/bin/build_mysql_conf
fi

/sbin/service mysql restart

%preun server

# Remove the service if no MySQL will be in place after we're done,
# Stop and remove the service
if test $1 = 0; then
    /sbin/service mysql stop || /bin/true
    /sbin/chkconfig --del mysql || /bin/true
fi

# We do not remove the mysql user since it may still own a lot of
# database files.

# Clean up the BuildRoot
%clean
[ "$RPM_BUILD_ROOT" != "/" ] && [ -d $RPM_BUILD_ROOT ] && rm -rf $RPM_BUILD_ROOT;

%files server
%defattr(-,root,root,0755)

%doc mysql-release-%{mysql_version}/COPYING mysql-release-%{mysql_version}/README 
%doc mysql-release-%{mysql_version}/support-files/my-*.cnf

%doc %attr(644, root, root) %{_infodir}/mysql.info*

%doc %attr(644, root, man) %{_mandir}/man1/innochecksum.1*
%doc %attr(644, root, man) %{_mandir}/man1/my_print_defaults.1*
%doc %attr(644, root, man) %{_mandir}/man1/myisam_ftdump.1*
%doc %attr(644, root, man) %{_mandir}/man1/myisamchk.1*
%doc %attr(644, root, man) %{_mandir}/man1/myisamlog.1*
%doc %attr(644, root, man) %{_mandir}/man1/myisampack.1*
%doc %attr(644, root, man) %{_mandir}/man8/mysqld.8*
%doc %attr(644, root, man) %{_mandir}/man1/mysqld_multi.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqld_safe.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_fix_privilege_tables.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_install_db.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_upgrade.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlhotcopy.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlman.1*
%doc %attr(644, root, man) %{_mandir}/man8/mysqlmanager.8*
%doc %attr(644, root, man) %{_mandir}/man1/mysql.server.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqltest.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_tzinfo_to_sql.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_zap.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlbug.1*
%doc %attr(644, root, man) %{_mandir}/man1/perror.1*
%doc %attr(644, root, man) %{_mandir}/man1/replace.1*
%doc %attr(644, root, man) %{_mandir}/man1/comp_err.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_convert_table_format.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_fix_extensions.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_secure_installation.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_setpermission.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_waitpid.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqldumpslow.1*
%doc %attr(644, root, man) %{_mandir}/man1/resolve_stack_dump.1*
%doc %attr(644, root, man) %{_mandir}/man1/resolveip.1*


%ghost %config(noreplace,missingok) %{_sysconfdir}/my.cnf
%ghost %config(noreplace,missingok) %{_sysconfdir}/mysqlmanager.passwd

%attr(755, root, root) %{_bindir}/innochecksum
%attr(755, root, root) %{_bindir}/my_print_defaults
%attr(755, root, root) %{_bindir}/myisam_ftdump
%attr(755, root, root) %{_bindir}/myisamchk
%attr(755, root, root) %{_bindir}/myisamlog
%attr(755, root, root) %{_bindir}/myisampack
%attr(755, root, root) %{_bindir}/mysql_convert_table_format
%attr(755, root, root) %{_bindir}/mysql_fix_extensions
%attr(755, root, root) %{_bindir}/mysql_fix_privilege_tables
%attr(755, root, root) %{_bindir}/mysql_install_db
%attr(755, root, root) %{_bindir}/mysql_secure_installation
%attr(755, root, root) %{_bindir}/mysql_setpermission
%attr(755, root, root) %{_bindir}/mysql_tzinfo_to_sql
%attr(755, root, root) %{_bindir}/mysql_upgrade
%attr(755, root, root) %{_bindir}/mysql_zap
%attr(755, root, root) %{_bindir}/mysqlbug
%attr(755, root, root) %{_bindir}/mysqld_multi
%attr(755, root, root) %{_bindir}/mysqld_safe
%attr(755, root, root) %{_bindir}/mysqldumpslow
%attr(755, root, root) %{_bindir}/mysqlhotcopy
%attr(755, root, root) %{_bindir}/mysqltest
%attr(755, root, root) %{_bindir}/perror
%attr(755, root, root) %{_bindir}/replace
%attr(755, root, root) %{_bindir}/resolve_stack_dump
%attr(755, root, root) %{_bindir}/resolveip

%attr(755, root, root) %{_libdir}/mysql/plugin/ha_example.so*
%attr(755, root, root) %{_libdir}/mysql/plugin/ha_innodb_plugin.so*

%attr(755, root, root) %{_sbindir}/mysqld
%attr(755, root, root) %{_sbindir}/mysqld-debug
%attr(755, root, root) %{_sbindir}/mysqlmanager
%attr(755, root, root) %{_sbindir}/rcmysql

%attr(644, root, root) %config(noreplace,missingok) %{_sysconfdir}/logrotate.d/mysql
%attr(755, root, root) %{_sysconfdir}/init.d/mysql

%attr(755, root, root) %{_datadir}/mysql/

%files client
%defattr(-, root, root, 0755)
%attr(755, root, root) %{_bindir}/msql2mysql
%attr(755, root, root) %{_bindir}/mysql
%attr(755, root, root) %{_bindir}/mysql_find_rows
%attr(755, root, root) %{_bindir}/mysql_waitpid
%attr(755, root, root) %{_bindir}/mysqlaccess
%attr(755, root, root) %{_bindir}/mysqladmin
%attr(755, root, root) %{_bindir}/mysqlbinlog
%attr(755, root, root) %{_bindir}/mysqlcheck
%attr(755, root, root) %{_bindir}/mysqldump
%attr(755, root, root) %{_bindir}/mysqlimport
%attr(755, root, root) %{_bindir}/mysqlshow
%attr(755, root, root) %{_bindir}/mysqlslap

%doc %attr(644, root, man) %{_mandir}/man1/msql2mysql.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql_find_rows.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlaccess.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqladmin.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlbinlog.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlcheck.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqldump.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlimport.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlshow.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysqlslap.1*

%post shared
/sbin/ldconfig

%postun shared
/sbin/ldconfig

%files devel
%defattr(-, root, root, 0755)
%doc %attr(644, root, man) %{_mandir}/man1/mysql_config.1*
%attr(755, root, root) %{_bindir}/mysql_config
%dir %attr(755, root, root) %{_includedir}/mysql
%dir %attr(755, root, root) %{_libdir}/mysql
%{_includedir}/mysql/*
%{_datadir}/aclocal/mysql.m4
%{_libdir}/mysql/libdbug.a
%{_libdir}/mysql/libheap.a
%if %{have_libgcc}
%{_libdir}/mysql/libmygcc.a
%endif
%{_libdir}/mysql/libmyisam.a
%{_libdir}/mysql/libmyisammrg.a
%{_libdir}/mysql/libmysqlclient.a
%{_libdir}/mysql/libmysqlclient.la
%{_libdir}/mysql/libmysqlclient_r.a
%{_libdir}/mysql/libmysqlclient_r.la
%{_libdir}/mysql/libmystrings.a
%{_libdir}/mysql/libmysys.a
%{_libdir}/mysql/libvio.a
%{_libdir}/mysql/libz.a
%{_libdir}/mysql/libz.la
%{_libdir}/mysql/plugin/ha_example.a
%{_libdir}/mysql/plugin/ha_example.la
%{_libdir}/mysql/plugin/ha_innodb_plugin.a
%{_libdir}/mysql/plugin/ha_innodb_plugin.la

%files shared
%defattr(-, root, root, 0755)
# Shared libraries (omit for architectures that don't support them)
%{_libdir}/libmysql*.so*

%files test
%defattr(-, root, root, 0755)
%attr(-, root, root) %{_datadir}/mysql-test
%attr(755, root, root) %{_bindir}/mysql_client_test
%doc %attr(644, root, man) %{_mandir}/man1/mysql_client_test.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql-stress-test.pl.1*
%doc %attr(644, root, man) %{_mandir}/man1/mysql-test-run.pl.1*

%files -n cl-MySQL-meta
%defattr(-, root, root, 0755)

%files -n cl-MySQL-meta-client
%defattr(-, root, root, 0755)

%files -n cl-MySQL-meta-devel
%defattr(-, root, root, 0755)

# The spec file changelog only includes changes made to the spec file
# itself - note that they must be ordered by date (important when
# merging BK trees)
%changelog
* Tue Feb 5 2013 Nicolas Rochelemagne <nicolas.rochelemagne@cpanel.net> 5.1.68-1.cp1136
- New upstream release

* Thu Dec 27 2012 Rikus Goodell <rikus.goodell@cpanel.net> 5.1.67-1.cp1136
- New upstream release
- Remove previous patch, as CVE-2012-5611 is addressed in 5.1.67.
- Put MySQL back into init system when RPM is renamed to MySQL51

* Tue Dec 11 2012 Nicolas Rochelemagne <nicolas.rochelemagne@cpanel.net> 5.1.66-2.cp1136
- patch for CVE-2012-5611 mysql: acl_get() stack-based buffer overflow

* Wed Oct 23 2012 Kyle Lafkoff <kyle.lafkoff@cpanel.net> - 5.1.66-1.cp1136
- Rename package from MySQL to MySQL51 to prevent packaging system confusion
- Obsolete MySQL package names
- Patch scripts to use /usr/local/cpanel/3rdparty/bin/perl
- add parallel build to default at -j6
- remove detection of perl dependencies during build.
- Add trigger for MySQL-server so mysqld is restarted when MySQL-server is removed

* Mon Oct 15 2012 brian m. carlson <brian.carlson@cpanel.net> 5.1.66-0.cloud
- New upstream release
- Rebased previous patches from last update.
- Removed YaSSL patch since the bug has been fixed upstream.

* Fri Aug 10 2012 brian m. carlson <brian.carlson@cpanel.net> 5.1.65-0.cloud
- New upstream release
- Rebased previous patches from last update.

* Thu May 7 2012 brian m. carlson <brian.carlson@cpanel.net> 5.1.63-0.cloud
- New upstream release
- Rebased previous patches from last update.

* Thu Apr 19 2012 brian m. carlson <brian.carlson@cpanel.net> 5.1.62-2.cloud
- Disabled inclusion of conflicting libcrypto symbols.

* Mon Apr 16 2012 brian m. carlson <brian.carlson@cpanel.net> 5.1.62-1.cloud
- Disabled userstats by default.

* Fri Mar 23 2012 John Lightsey <jd@cpanel.net> 5.1.62-0.cloud
- New upstream release
- Rebased previous patches from last update.

* Thu Jan 19 2012 Kyle Lafkoff <kyle.lafkoff@cpanel.net> 5.1.61-0.cloud
- New upstream release
- Rebased previous patches from last update.

* Fri Sep 23 2011 Kyle Lafkoff <kyle.lafkoff@cpanel.net> 5.1.59-0.cloud
- New upstream release
- Rename revision to reflect cloud linux patches
- Because this build will have cloud linux patches, it will only be built for CentHat 4-6. As a result,
  legacy compatibility patches have been removed (gcc_296_operator_delete.patch, SYS_gettid-constant.patch)
- Applied Cloud Linux patches: 
-  0002-Cloud-Linux-userstat_mysql.patch
-  0003-Cloud-Linux-max_connection2.patch
-  Auto Generated: 0004-autogen.patch

* Fri Jul 8 2011 Todd Rinaldo <toddr@cpanel.net> 5.1.58-0
- New upstream release

* Thu May 12 2011 Todd Rinaldo <toddr@cpanel.net> 5.1.57-0
- New upstream release

* Tue Mar 7 2011 Todd Rinaldo <toddr@cpanel.net> 5.1.56-0
- New upstream release

* Tue Feb 8 2011 Todd Rinaldo <toddr@cpanel.net> 5.1.55-0
- New upstream release
- upstream started using SYS_gettid stacktrace.c which isn't present
  in pre-AS3. Patch it back off in pre-AS3 - MySQL bug 60171

* Tue Dec 15 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.54-0
- New upstream release
- Add -Wno-unused-parameter to CXXFLAGS per \#mysql-dev
- Add patch pointer_patch_5154.patch for Mysql bug 57990

* Tue Dec 14 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.53-0
- New upstream release
- Build never succeeded: storage/archive/ha_archive.cc

* Tue Nov 3 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.52-0
- New upstream release

* Tue Sep 28 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.51-0
- New upstream release
- Patch for bug 55846 accepted upstream and removed from this release

* Thu Sep 23 2010 John Lightsey <jd@cpanel.net> 5.1.50-1
- Apply patch for http://bugs.mysql.com/bug.php?id=55846

* Tue Aug 31 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.50-0
- New upstream release

* Tue Aug 3 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.49-0
- New upstream release

* Thu Jun 17 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.48-0
- New upstream release

* Fri May 21 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.47-0
- New upstream release
- Upstream seems to have absorbed patch gcc_init_vars_before_code.mysql.5.1.46.patch

* Mon Apr 26 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.46-0
- New upstream release
- mysql 5.1.46 - patch 2 new c files that declare variables mid-function which breaks older compilers

* Mon Mar 22 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.45-0
- New upstream release
- Quiet tar extract

* Thu Feb 18 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.44-0
- New upstream release
- all unpackaged files removed
- define _unpackaged_files_terminate_build 0 turned off so we can see when files are added.

* Mon Feb 1 2010 Todd Rinaldo <toddr@cpanel.net> 5.1.43-0
- New upstream release
- patch mysql-5.1-gcc-2.95.patch absorbed by upstream
- patch gcc_296_operator_delete.patch will remain: "5.1 has dropped support for GCC 2.96 (not that they won't work) which means that fixes for old compilers won't be included"
- Removed support for optional CLUSTER/YASSL/EMBEDDED/NDB. Hard coded to the cpanel way in spec file.
- Trustix 2 segfaults during build. We're going to exclude it from this build run and see how it goes next time around.
- Build wrapper was causing breaks. spec file simplified. Should be more clear how the build process works for this.
- tried and failed --with-plugin= this caused innodb not to be built with the binary.

* Wed Dec 2 2009 Todd Rinaldo <toddr@cpanel.net> 5.1.41-0
- New upstream release
- Update patching via git now.
- Patches standard -p1 now.
- Pull spec file from upstream as of 5.1.41 force charsets for be all regardless of cluster build
- Monitoring MySQL bug giving bogus configure warning messages: http://bugs.mysql.com/bug.php?id=42872
- innodb plugin hardcoded on
- zlib always bundled.
- gcc_296_operator_delete.patch from MySQL 5.0 now seems to be required for gcc 2.96 envs.
- add --without-mysqlmanager to debug build since not only do we never use the code, but it's breaking on gcc 2.96
- mandrake 8.2 is breaking for compile due to -O3 option. Switching to -O2 for ALL gcc 2.96

* Mon Oct 26 2009 Todd Rinaldo <toddr@cpanel.net> 5.1.40-0
- New upstream release
- Patch submitted to mysql folks for gcc fix

* Mon Sep 23 2009 John Lightsey <jd@cpanel.net> 5.1.39-0
- New upstream release
- Update mysql-5.1-gcc-2.95.patch

* Mon Sep 08 2009 John Lightsey <jd@cpanel.net> 5.1.38-0
- New upstream release
- Update mysql-5.1.38-gcc-2.95.patch

* Mon Aug 24 2009 Jonathan Perkin <jperkin@sun.com>

- Add conditionals for bundled zlib and innodb plugin

* Fri Aug 21 2009 Jonathan Perkin <jperkin@sun.com>

- Install plugin libraries in appropriate packages.
- Disable libdaemon_example and ftexample plugins.

* Thu Aug 20 2009 Jonathan Perkin <jperkin@sun.com>

- Update variable used for mysql-test suite location to match source.

* Mon Aug 03 2009 John Lightsey <jd@cpanel.net> 5.1.37-0
- New upstream release
- Update mysql-5.1.37-gcc-2.95.patch

* Thu Jul 02 2009 John Lightsey <jd@cpanel.net> 5.1.36-0
- New upstream release
- Update mysql-5.1.36-gcc-2.95.patch

* Mon Jun 08 2009 John Lightsey <jd@cpanel.net> 5.1.35-0
- New upstream release
- Update mysql-5.1.35-gcc-2.95.patch

* Tue Apr 21 2009 John Lightsey <jd@cpanel.net> 5.1.34-0
- New upstream release
- Update mysql-5.1.34-gcc-2.95.patch

* Mon Apr 06 2009 John Lightsey <jd@cpanel.net> 5.1.33-0
- New upstream release
- Update mysql-5.1.33-gcc-2.95.patch

* Tue Mar 17 2009 John Lightsey <jd@cpanel.net> 5.1.32-0
- New upstream release
- Update mysql-5.1.32-gcc-2.95.patch

* Mon Dec 15 2008 John Lightsey <jd@cpanel.net> 5.1.30-0
- New upstream release
- Add conditional compilation of embedded package
- Switch conditional logic to build with YASSL support by default
- Suppress testing during RPM build process
- Add mysql-5.1.30-gcc-2.95.patch to remove C99 syntax

* Fri Nov 07 2008 Joerg Bruehe <joerg@mysql.com>

- Correct yesterday's fix, so that it also works for the last flag,
  and fix a wrong quoting: un-quoted quote marks must not be escaped.
  
* Thu Nov 06 2008 Kent Boortz <kent.boortz@sun.com>

- Removed "mysql_upgrade_shell"
- Removed some copy/paste between debug and normal build

* Thu Nov 06 2008 Joerg Bruehe <joerg@mysql.com>

- Modify CFLAGS and CXXFLAGS such that a debug build is not optimized.
  This should cover both gcc and icc flags.  Fixes bug#40546.
  
* Fri Aug 29 2008 Kent Boortz <kent@mysql.com>

- Removed the "Federated" storage engine option, and enabled in all

* Tue Aug 26 2008 Joerg Bruehe <joerg@mysql.com>

- Get rid of the "warning: Installed (but unpackaged) file(s) found:"
  Some generated files aren't needed in RPMs:
  - the "sql-bench/" subdirectory
  Some files were missing:
  - /usr/share/aclocal/mysql.m4  ("devel" subpackage)
  - Manual "mysqlbug" ("server" subpackage)
  - Program "innochecksum" and its manual ("server" subpackage)
  - Manual "mysql_find_rows" ("client" subpackage)
  - Script "mysql_upgrade_shell" ("client" subpackage)
  - Program "ndb_cpcd" and its manual ("ndb-extra" subpackage)
  - Manuals "ndb_mgm" + "ndb_restore" ("ndb-tools" subpackage)

* Mon Mar 31 2008 Kent Boortz <kent@mysql.com>

- Made the "Federated" storage engine an option
- Made the "Cluster" storage engine and sub packages an option

* Wed Mar 19 2008 Joerg Bruehe <joerg@mysql.com>

- Add the man pages for "ndbd" and "ndb_mgmd".

* Mon Feb 18 2008 Timothy Smith <tim@mysql.com>

- Require a manual upgrade if the alread-installed mysql-server is
  from another vendor, or is of a different major version.

* Wed May 02 2007 Joerg Bruehe <joerg@mysql.com>

- "ndb_size.tmpl" is not needed any more, 
  "man1/mysql_install_db.1" lacked the trailing '*'.

* Sat Apr 07 2007 Kent Boortz <kent@mysql.com>

- Removed man page for "mysql_create_system_tables"

* Wed Mar 21 2007 Daniel Fischer <df@mysql.com>

- Add debug server.

* Mon Mar 19 2007 Daniel Fischer <df@mysql.com>

- Remove Max RPMs; the server RPMs contain a mysqld compiled with all
  features that previously only were built into Max.

* Fri Mar 02 2007 Joerg Bruehe <joerg@mysql.com>

- Add several man pages for NDB which are now created.

* Fri Jan 05 2007 Kent Boortz <kent@mysql.com>

- Put back "libmygcc.a", found no real reason it was removed.

- Add CFLAGS to gcc call with --print-libgcc-file, to make sure the
  correct "libgcc.a" path is returned for the 32/64 bit architecture.

* Mon Dec 18 2006 Joerg Bruehe <joerg@mysql.com>

- Fix the move of "mysqlmanager" to section 8: Directory name was wrong.

* Thu Dec 14 2006 Joerg Bruehe <joerg@mysql.com>

- Include the new man pages for "my_print_defaults" and "mysql_tzinfo_to_sql"
  in the server RPM.
- The "mysqlmanager" man page got moved from section 1 to 8.

* Thu Nov 30 2006 Joerg Bruehe <joerg@mysql.com>

- Call "make install" using "benchdir_root=%{_datadir}", 
  because that is affecting the regression test suite as well.

* Thu Nov 16 2006 Joerg Bruehe <joerg@mysql.com>

- Explicitly note that the "MySQL-shared" RPMs (as built by MySQL AB) 
  replace "mysql-shared" (as distributed by SuSE) to allow easy upgrading
  (bug#22081).

* Mon Nov 13 2006 Joerg Bruehe <joerg@mysql.com>

- Add "--with-partition" to all server builds.

- Use "--report-features" in one test run per server build.

* Tue Aug 15 2006 Joerg Bruehe <joerg@mysql.com>

- The "max" server is removed from packages, effective from 5.1.12-beta.
  Delete all steps to build, package, or install it.

* Mon Jul 10 2006 Joerg Bruehe <joerg@mysql.com>

- Fix a typing error in the "make" target for the Perl script to run the tests.

* Tue Jul 04 2006 Joerg Bruehe <joerg@mysql.com>

- Use the Perl script to run the tests, because it will automatically check
  whether the server is configured with SSL.

* Tue Jun 27 2006 Joerg Bruehe <joerg@mysql.com>

- move "mysqldumpslow" from the client RPM to the server RPM (bug#20216)

- Revert all previous attempts to call "mysql_upgrade" during RPM upgrade,
  there are some more aspects which need to be solved before this is possible.
  For now, just ensure the binary "mysql_upgrade" is delivered and installed.

* Thu Jun 22 2006 Joerg Bruehe <joerg@mysql.com>

- Close a gap of the previous version by explicitly using
  a newly created temporary directory for the socket to be used
  in the "mysql_upgrade" operation, overriding any local setting.

* Tue Jun 20 2006 Joerg Bruehe <joerg@mysql.com>

- To run "mysql_upgrade", we need a running server;
  start it in isolation and skip password checks.

* Sat May 20 2006 Kent Boortz <kent@mysql.com>

- Always compile for PIC, position independent code.

* Wed May 10 2006 Kent Boortz <kent@mysql.com>

- Use character set "all" when compiling with Cluster, to make Cluster
  nodes independent on the character set directory, and the problem
  that two RPM sub packages both wants to install this directory.

* Mon May 01 2006 Kent Boortz <kent@mysql.com>

- Use "./libtool --mode=execute" instead of searching for the
  executable in current directory and ".libs".

* Fri Apr 28 2006 Kent Boortz <kent@mysql.com>

- Install and run "mysql_upgrade"

* Wed Apr 12 2006 Jim Winstead <jimw@mysql.com>

- Remove sql-bench, and MySQL-bench RPM (will be built as an independent
  project from the mysql-bench repository)

* Tue Apr 11 2006 Jim Winstead <jimw@mysql.com>

- Remove old mysqltestmanager and related programs
* Sat Apr 01 2006 Kent Boortz <kent@mysql.com>

- Set $LDFLAGS from $MYSQL_BUILD_LDFLAGS

* Wed Mar 07 2006 Kent Boortz <kent@mysql.com>

- Changed product name from "Community Edition" to "Community Server"

* Mon Mar 06 2006 Kent Boortz <kent@mysql.com>

- Fast mutexes is now disabled by default, but should be
  used in Linux builds.

* Mon Feb 20 2006 Kent Boortz <kent@mysql.com>

- Reintroduced a max build
- Limited testing of 'debug' and 'max' servers
- Berkeley DB only in 'max'

* Mon Feb 13 2006 Joerg Bruehe <joerg@mysql.com>

- Use "-i" on "make test-force";
  this is essential for later evaluation of this log file.

* Thu Feb 09 2006 Kent Boortz <kent@mysql.com>

- Pass '-static' to libtool, link static with our own libraries, dynamic
  with system libraries.  Link with the bundled zlib.

* Wed Feb 08 2006 Kristian Nielsen <knielsen@mysql.com>

- Modified RPM spec to match new 5.1 debug+max combined community packaging.

* Sun Dec 18 2005 Kent Boortz <kent@mysql.com>

- Added "client/mysqlslap"

* Mon Dec 12 2005 Rodrigo Novo <rodrigo@mysql.com>

- Added zlib to the list of (static) libraries installed
- Added check against libtool wierdness (WRT: sql/mysqld || sql/.libs/mysqld)
- Compile MySQL with bundled zlib
- Fixed %packager name to "MySQL Production Engineering Team"

* Mon Dec 05 2005 Joerg Bruehe <joerg@mysql.com>

- Avoid using the "bundled" zlib on "shared" builds: 
  As it is not installed (on the build system), this gives dependency 
  problems with "libtool" causing the build to fail.
  (Change was done on Nov 11, but left uncommented.)

* Tue Nov 22 2005 Joerg Bruehe <joerg@mysql.com>

- Extend the file existence check for "init.d/mysql" on un-install
  to also guard the call to "insserv"/"chkconfig".

* Thu Oct 27 2005 Lenz Grimmer <lenz@grimmer.com>

- added more man pages

* Wed Oct 19 2005 Kent Boortz <kent@mysql.com>

- Made yaSSL support an option (off by default)

* Wed Oct 19 2005 Kent Boortz <kent@mysql.com>

- Enabled yaSSL support

* Sat Oct 15 2005 Kent Boortz <kent@mysql.com>

- Give mode arguments the same way in all places
- Moved copy of mysqld.a to "standard" build, but
  disabled it as we don't do embedded yet in 5.0

* Fri Oct 14 2005 Kent Boortz <kent@mysql.com>

- For 5.x, always compile with --with-big-tables
- Copy the config.log file to location outside
  the build tree

* Fri Oct 14 2005 Kent Boortz <kent@mysql.com>

- Removed unneeded/obsolete configure options
- Added archive engine to standard server
- Removed the embedded server from experimental server
- Changed suffix "-Max" => "-max"
- Changed comment string "Max" => "Experimental"

* Thu Oct 13 2005 Lenz Grimmer <lenz@mysql.com>

- added a usermod call to assign a potential existing mysql user to the
  correct user group (BUG#12823)
- Save the perror binary built during Max build so it supports the NDB
  error codes (BUG#13740)
- added a separate macro "mysqld_group" to be able to define the
  user group of the mysql user seperately, if desired.

* Thu Sep 29 2005 Lenz Grimmer <lenz@mysql.com>

- fixed the removing of the RPM_BUILD_ROOT in the %clean section (the
  $RBR variable did not get expanded, thus leaving old build roots behind)

* Thu Aug 04 2005 Lenz Grimmer <lenz@mysql.com>

- Fixed the creation of the mysql user group account in the postinstall
  section (BUG 12348)
- Fixed enabling the Archive storage engine in the Max binary

* Tue Aug 02 2005 Lenz Grimmer <lenz@mysql.com>

- Fixed the Requires: tag for the server RPM (BUG 12233)

* Fri Jul 15 2005 Lenz Grimmer <lenz@mysql.com>

- create a "mysql" user group and assign the mysql user account to that group
  in the server postinstall section. (BUG 10984)

* Tue Jun 14 2005 Lenz Grimmer <lenz@mysql.com>

- Do not build statically on i386 by default, only when adding either "--with
  static" or "--define '_with_static 1'" to the RPM build options. Static
  linking really only makes sense when linking against the specially patched
  glibc 2.2.5.

* Mon Jun 06 2005 Lenz Grimmer <lenz@mysql.com>

- added mysql_client_test to the "bench" subpackage (BUG 10676)
- added the libndbclient static and shared libraries (BUG 10676)

* Wed Jun 01 2005 Lenz Grimmer <lenz@mysql.com>

- use "mysqldatadir" variable instead of hard-coding the path multiple times
- use the "mysqld_user" variable on all occasions a user name is referenced
- removed (incomplete) Brazilian translations
- removed redundant release tags from the subpackage descriptions

* Wed May 25 2005 Joerg Bruehe <joerg@mysql.com>

- Added a "make clean" between separate calls to "BuildMySQL".

* Thu May 12 2005 Guilhem Bichot <guilhem@mysql.com>

- Removed the mysql_tableinfo script made obsolete by the information schema

* Wed Apr 20 2005 Lenz Grimmer <lenz@mysql.com>

- Enabled the "blackhole" storage engine for the Max RPM

* Wed Apr 13 2005 Lenz Grimmer <lenz@mysql.com>

- removed the MySQL manual files (html/ps/texi) - they have been removed
  from the MySQL sources and are now available seperately.

* Mon Apr 4 2005 Petr Chardin <petr@mysql.com>

- old mysqlmanager, mysqlmanagerc and mysqlmanager-pwger renamed into
  mysqltestmanager, mysqltestmanager and mysqltestmanager-pwgen respectively

* Fri Mar 18 2005 Lenz Grimmer <lenz@mysql.com>

- Disabled RAID in the Max binaries once and for all (it has finally been
  removed from the source tree)

* Sun Feb 20 2005 Petr Chardin <petr@mysql.com>

- Install MySQL Instance Manager together with mysqld, touch mysqlmanager
  password file

* Mon Feb 14 2005 Lenz Grimmer <lenz@mysql.com>

- Fixed the compilation comments and moved them into the separate build sections
  for Max and Standard

* Mon Feb 7 2005 Tomas Ulin <tomas@mysql.com>

- enabled the "Ndbcluster" storage engine for the max binary
- added extra make install in ndb subdir after Max build to get ndb binaries
- added packages for ndbcluster storage engine

* Fri Jan 14 2005 Lenz Grimmer <lenz@mysql.com>

- replaced obsoleted "BuildPrereq" with "BuildRequires" instead

* Thu Jan 13 2005 Lenz Grimmer <lenz@mysql.com>

- enabled the "Federated" storage engine for the max binary

* Tue Jan 04 2005 Petr Chardin <petr@mysql.com>

- ISAM and merge storage engines were purged. As well as appropriate
  tools and manpages (isamchk and isamlog)

* Thu Dec 31 2004 Lenz Grimmer <lenz@mysql.com>

- enabled the "Archive" storage engine for the max binary
- enabled the "CSV" storage engine for the max binary
- enabled the "Example" storage engine for the max binary

* Thu Aug 26 2004 Lenz Grimmer <lenz@mysql.com>

- MySQL-Max now requires MySQL-server instead of MySQL (BUG 3860)

* Fri Aug 20 2004 Lenz Grimmer <lenz@mysql.com>

- do not link statically on IA64/AMD64 as these systems do not have
  a patched glibc installed

* Tue Aug 10 2004 Lenz Grimmer <lenz@mysql.com>

- Added libmygcc.a to the devel subpackage (required to link applications
  against the the embedded server libmysqld.a) (BUG 4921)

* Mon Aug 09 2004 Lenz Grimmer <lenz@mysql.com>

- Added EXCEPTIONS-CLIENT to the "devel" package

* Thu Jul 29 2004 Lenz Grimmer <lenz@mysql.com>

- disabled OpenSSL in the Max binaries again (the RPM packages were the
  only exception to this anyway) (BUG 1043)

* Wed Jun 30 2004 Lenz Grimmer <lenz@mysql.com>

- fixed server postinstall (mysql_install_db was called with the wrong
  parameter)

* Thu Jun 24 2004 Lenz Grimmer <lenz@mysql.com>

- added mysql_tzinfo_to_sql to the server subpackage
- run "make clean" instead of "make distclean"

* Mon Apr 05 2004 Lenz Grimmer <lenz@mysql.com>

- added ncurses-devel to the build prerequisites (BUG 3377)

* Thu Feb 12 2004 Lenz Grimmer <lenz@mysql.com>

- when using gcc, _always_ use CXX=gcc 
- replaced Copyright with License field (Copyright is obsolete)

* Tue Feb 03 2004 Lenz Grimmer <lenz@mysql.com>

- added myisam_ftdump to the Server package

* Tue Jan 13 2004 Lenz Grimmer <lenz@mysql.com>

- link the mysql client against libreadline instead of libedit (BUG 2289)

* Mon Dec 22 2003 Lenz Grimmer <lenz@mysql.com>

- marked /etc/logrotate.d/mysql as a config file (BUG 2156)

* Fri Dec 13 2003 Lenz Grimmer <lenz@mysql.com>

- fixed file permissions (BUG 1672)

* Thu Dec 11 2003 Lenz Grimmer <lenz@mysql.com>

- made testing for gcc3 a bit more robust

* Fri Dec 05 2003 Lenz Grimmer <lenz@mysql.com>

- added missing file mysql_create_system_tables to the server subpackage

* Fri Nov 21 2003 Lenz Grimmer <lenz@mysql.com>

- removed dependency on MySQL-client from the MySQL-devel subpackage
  as it is not really required. (BUG 1610)

* Fri Aug 29 2003 Lenz Grimmer <lenz@mysql.com>

- Fixed BUG 1162 (removed macro names from the changelog)
- Really fixed BUG 998 (disable the checking for installed but
  unpackaged files)

* Tue Aug 05 2003 Lenz Grimmer <lenz@mysql.com>

- Fixed BUG 959 (libmysqld not being compiled properly)
- Fixed BUG 998 (RPM build errors): added missing files to the
  distribution (mysql_fix_extensions, mysql_tableinfo, mysqldumpslow,
  mysql_fix_privilege_tables.1), removed "-n" from install section.

* Wed Jul 09 2003 Lenz Grimmer <lenz@mysql.com>

- removed the GIF Icon (file was not included in the sources anyway)
- removed unused variable shared_lib_version
- do not run automake before building the standard binary
  (should not be necessary)
- add server suffix '-standard' to standard binary (to be in line
  with the binary tarball distributions)
- Use more RPM macros (_exec_prefix, _sbindir, _libdir, _sysconfdir,
  _datadir, _includedir) throughout the spec file.
- allow overriding CC and CXX (required when building with other compilers)

* Fri May 16 2003 Lenz Grimmer <lenz@mysql.com>

- re-enabled RAID again

* Wed Apr 30 2003 Lenz Grimmer <lenz@mysql.com>

- disabled MyISAM RAID (--with-raid) - it throws an assertion which
  needs to be investigated first.

* Mon Mar 10 2003 Lenz Grimmer <lenz@mysql.com>

- added missing file mysql_secure_installation to server subpackage
  (BUG 141)

* Tue Feb 11 2003 Lenz Grimmer <lenz@mysql.com>

- re-added missing pre- and post(un)install scripts to server subpackage
- added config file /etc/my.cnf to the file list (just for completeness)
- make sure to create the datadir with 755 permissions

* Mon Jan 27 2003 Lenz Grimmer <lenz@mysql.com>

- removed unused CC and CXX variables
- CFLAGS and CXXFLAGS should honor RPM_OPT_FLAGS

* Fri Jan 24 2003 Lenz Grimmer <lenz@mysql.com>

- renamed package "MySQL" to "MySQL-server"
- fixed Copyright tag
- added mysql_waitpid to client subpackage (required for mysql-test-run)

* Wed Nov 27 2002 Lenz Grimmer <lenz@mysql.com>

- moved init script from /etc/rc.d/init.d to /etc/init.d (the majority of 
  Linux distributions now support this scheme as proposed by the LSB either
  directly or via a compatibility symlink)
- Use new "restart" init script action instead of starting and stopping
  separately
- Be more flexible in activating the automatic bootup - use insserv (on
  older SuSE versions) or chkconfig (Red Hat, newer SuSE versions and
  others) to create the respective symlinks

* Wed Sep 25 2002 Lenz Grimmer <lenz@mysql.com>

- MySQL-Max now requires MySQL >= 4.0 to avoid version mismatches
  (mixing 3.23 and 4.0 packages)

* Fri Aug 09 2002 Lenz Grimmer <lenz@mysql.com>
 
- Turn off OpenSSL in MySQL-Max for now until it works properly again
- enable RAID for the Max binary instead
- added compatibility link: safe_mysqld -> mysqld_safe to ease the
  transition from 3.23

* Thu Jul 18 2002 Lenz Grimmer <lenz@mysql.com>

- Reworked the build steps a little bit: the Max binary is supposed
  to include OpenSSL, which cannot be linked statically, thus trying
	to statically link against a special glibc is futile anyway
- because of this, it is not required to make yet another build run
  just to compile the shared libs (saves a lot of time)
- updated package description of the Max subpackage
- clean up the BuildRoot directory afterwards

* Mon Jul 15 2002 Lenz Grimmer <lenz@mysql.com>

- Updated Packager information
- Fixed the build options: the regular package is supposed to
  include InnoDB and linked statically, while the Max package
	should include BDB and SSL support

* Fri May 03 2002 Lenz Grimmer <lenz@mysql.com>

- Use more RPM macros (e.g. infodir, mandir) to make the spec
  file more portable
- reorganized the installation of documentation files: let RPM
  take care of this
- reorganized the file list: actually install man pages along
  with the binaries of the respective subpackage
- do not include libmysqld.a in the devel subpackage as well, if we
  have a special "embedded" subpackage
- reworked the package descriptions

* Mon Oct  8 2001 Monty

- Added embedded server as a separate RPM

* Fri Apr 13 2001 Monty

- Added mysqld-max to the distribution

* Tue Jan 2  2001  Monty

- Added mysql-test to the bench package

* Fri Aug 18 2000 Tim Smith <tim@mysql.com>

- Added separate libmysql_r directory; now both a threaded
  and non-threaded library is shipped.

* Wed Sep 28 1999 David Axmark <davida@mysql.com>

- Added the support-files/my-example.cnf to the docs directory.

- Removed devel dependency on base since it is about client
  development.

* Wed Sep 8 1999 David Axmark <davida@mysql.com>

- Cleaned up some for 3.23.

* Thu Jul 1 1999 David Axmark <davida@mysql.com>

- Added support for shared libraries in a separate sub
  package. Original fix by David Fox (dsfox@cogsci.ucsd.edu)

- The --enable-assembler switch is now automatically disables on
  platforms there assembler code is unavailable. This should allow
  building this RPM on non i386 systems.

* Mon Feb 22 1999 David Axmark <david@detron.se>

- Removed unportable cc switches from the spec file. The defaults can
  now be overridden with environment variables. This feature is used
  to compile the official RPM with optimal (but compiler version
  specific) switches.

- Removed the repetitive description parts for the sub rpms. Maybe add
  again if RPM gets a multiline macro capability.

- Added support for a pt_BR translation. Translation contributed by
  Jorge Godoy <jorge@bestway.com.br>.

* Wed Nov 4 1998 David Axmark <david@detron.se>

- A lot of changes in all the rpm and install scripts. This may even
  be a working RPM :-)

* Sun Aug 16 1998 David Axmark <david@detron.se>

- A developers changelog for MySQL is available in the source RPM. And
  there is a history of major user visible changed in the Reference
  Manual.  Only RPM specific changes will be documented here.
