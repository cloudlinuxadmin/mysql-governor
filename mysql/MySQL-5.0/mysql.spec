Name: mysql
Version: 5.0.95
Release: 13%{?dist}.cloudlinux
Summary: MySQL client programs and shared libraries
Group: Applications/Databases
URL: http://www.mysql.com
# exceptions allow client libraries to be linked with most open source SW,
# not only GPL code.  See README.mysql-license
License: GPLv2 with exceptions

# Regression tests take a long time, you can skip 'em with this
%{!?runselftest:%define runselftest 0}

Source0: http://dev.mysql.com/get/Downloads/MySQL-5.0/mysql-%{version}.tar.gz
Source1: mysql.init
Source3: my.cnf
Source4: scriptstub.c
Source5: my_config.h
Source7: README.mysql-license
# Working around perl dependency checking bug in rpm FTTB. Remove later.
Source999: filter-requires-mysql.sh 
Patch1: mysql-libdir.patch
Patch2: mysql-errno.patch
Patch3: mysql-stack.patch
Patch4: mysql-testing.patch
Patch5: mysql-no-atomic.patch
Patch6: mysql-rpl_ddl.patch
Patch7: mysql-rpl-test.patch
Patch8: mysql-install-test.patch
Patch9: mysql-bdb-link.patch
Patch10: mysql-strmov.patch
Patch12: mysql-s390-truncate.patch
Patch13: mysql-no-dbug.patch
Patch15: mysql-stack-guard.patch
Patch16: mysql-expired-certs.patch
Patch22: mysql-cve-2010-1626.patch
Patch25: mysql-cve-2010-3680.patch
Patch26: mysql-cve-2010-3681.patch
Patch33: mysql-cve-2010-3839.patch
Patch38: mysql-more-blobs.patch
#Patch100: userstatv2.patch
Patch101: max_connection2_mysql_5_0_95_b400.4.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: /sbin/ldconfig, /sbin/install-info, grep, fileutils, chkconfig
BuildRequires: perl, readline-devel, openssl-devel bison
BuildRequires: gcc-c++, ncurses-devel, zlib-devel
BuildRequires: libtool automake autoconf gawk
# make test requires time
BuildRequires: time

Requires: bash
Conflicts: MySQL
Obsoletes: mysql-client mysql-perl

# Working around perl dependency checking bug in rpm FTTB. Remove later.
%define __perl_requires %{SOURCE999}

%description
MySQL is a multi-user, multi-threaded SQL database server. MySQL is a
client/server implementation consisting of a server daemon (mysqld)
and many different client programs and libraries. The base package
contains the MySQL client programs, the client shared libraries, and
generic MySQL files.

%package server

Summary: The MySQL server and related files
Group: Applications/Databases
Requires: /sbin/chkconfig, /usr/sbin/useradd
Requires: %{name} = %{version}-%{release}
Requires: sh-utils
# mysqlhotcopy needs DBI/DBD support
Requires: perl-DBI, perl-DBD-MySQL
Conflicts: MySQL-server

%description server
MySQL is a multi-user, multi-threaded SQL database server. MySQL is a
client/server implementation consisting of a server daemon (mysqld)
and many different client programs and libraries. This package contains
the MySQL server and some accompanying files and directories.

%package devel

Summary: Files for development of MySQL applications
Group: Applications/Databases
Requires: %{name} = %{version}-%{release}
Requires: openssl-devel
Conflicts: MySQL-devel

%description devel
MySQL is a multi-user, multi-threaded SQL database server. This
package contains the libraries and header files that are needed for
developing MySQL client applications.

%package bench

Summary: MySQL benchmark scripts and data
Group: Applications/Databases
Requires: %{name} = %{version}-%{release}
Conflicts: MySQL-bench

%description bench
MySQL is a multi-user, multi-threaded SQL database server. This
package contains benchmark scripts and data for use when benchmarking
MySQL.

%package test

Summary: The test suite distributed with MySQL
Group: Applications/Databases
Requires: %{name} = %{version}-%{release}
Requires: %{name}-server = %{version}-%{release}
Conflicts: MySQL-test

%description test
MySQL is a multi-user, multi-threaded SQL database server. This
package contains the regression test suite distributed with
the MySQL sources.

%prep
%setup -q 

%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch9 -p1
%patch10 -p1
%patch12 -p1
%patch13 -p1
%patch15 -p1
%patch16 -p1
%patch22 -p1
%patch25 -p1
%patch26 -p1
%patch33 -p1
%patch38 -p1
#%patch100 -p1
%patch101 -p1

libtoolize --force
aclocal
automake --add-missing
autoconf
autoheader

%build

# fail quickly and obviously if user tries to build as root
%if %runselftest
	if [ x"`id -u`" = x0 ]; then
		echo "mysql's regression tests fail if run as root."
		echo "If you really need to build the RPM as root, use"
		echo "--define='runselftest 0' to skip the regression tests."
		exit 1
	fi
%endif

CFLAGS="%{optflags} -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64 -D_LARGEFILE_SOURCE"
# MySQL 4.1.10 definitely doesn't work under strict aliasing; also,
# gcc 4.1 breaks MySQL 5.0.16 without -fwrapv
CFLAGS="$CFLAGS -fno-strict-aliasing -fwrapv"
%ifarch alpha
# Can't link C++ objects into an executable without this. Odd!
# -ECL 2002-12-19
CFLAGS="$CFLAGS -fPIC"
%endif
# Temporary workaround for gcc bug (bz #193912)
%ifarch s390x
CFLAGS="$CFLAGS -mtune=z900"
%endif
CXXFLAGS="$CFLAGS -fno-rtti -fno-exceptions"
export CFLAGS CXXFLAGS

%configure \
	--with-readline \
	--with-openssl \
	--without-debug \
	--enable-shared \
	--with-bench \
	--localstatedir=/var/lib/mysql \
	--with-unix-socket-path=/var/lib/mysql/mysql.sock \
	--with-mysqld-user="mysql" \
	--with-extra-charsets=all \
	--with-innodb \
	--with-berkeley-db \
	--enable-local-infile \
	--enable-largefile \
	--enable-thread-safe-client \
	--disable-dependency-tracking \
	--with-named-thread-libs="-lpthread"

gcc $CFLAGS $LDFLAGS -o scriptstub "-DLIBDIR=\"%{_libdir}/mysql\"" %{SOURCE4}

# Not enabling assembler

make %{?_smp_mflags}
make check

%if %runselftest
  # hack to let 32- and 64-bit tests run concurrently on same build machine
  case `uname -m` in
    ppc64 | s390x | x86_64)
      MTR_BUILD_THREAD=7
      ;;
    *)
      MTR_BUILD_THREAD=11
      ;;
  esac
  export MTR_BUILD_THREAD

  make test
%endif

%install
rm -rf $RPM_BUILD_ROOT

%makeinstall

# multilib header hack
# we only apply this to known Red Hat multilib arches, per bug #181335
case `uname -i` in
  i386 | x86_64 | ppc | ppc64 | s390 | s390x)
    install -m 644 include/my_config.h $RPM_BUILD_ROOT/usr/include/mysql/my_config_`uname -i`.h
    install -m 644 %{SOURCE5} $RPM_BUILD_ROOT/usr/include/mysql/
    ;;
  *)
    ;;
esac

mkdir -p $RPM_BUILD_ROOT/var/log
touch $RPM_BUILD_ROOT/var/log/mysqld.log

# List the installed tree for RPM package maintenance purposes.
find $RPM_BUILD_ROOT -print | sed "s|^$RPM_BUILD_ROOT||" | sort > ROOTFILES

gzip ${RPM_BUILD_ROOT}%{_infodir}/*

mkdir -p $RPM_BUILD_ROOT/etc/rc.d/init.d
mkdir -p $RPM_BUILD_ROOT/var/run/mysqld
install -m 0755 -d $RPM_BUILD_ROOT/var/lib/mysql
install -m 0755 %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/mysqld
install -m 0644 %{SOURCE3} $RPM_BUILD_ROOT/etc/my.cnf
rm -f $RPM_BUILD_ROOT/%{_infodir}/dir*
mv $RPM_BUILD_ROOT/usr/sql-bench $RPM_BUILD_ROOT%{_datadir}/sql-bench
mv $RPM_BUILD_ROOT/usr/mysql-test $RPM_BUILD_ROOT%{_datadir}/mysql-test

mv ${RPM_BUILD_ROOT}%{_bindir}/mysqlbug ${RPM_BUILD_ROOT}%{_libdir}/mysql/mysqlbug
install -m 0755 scriptstub ${RPM_BUILD_ROOT}%{_bindir}/mysqlbug
mv ${RPM_BUILD_ROOT}%{_bindir}/mysql_config ${RPM_BUILD_ROOT}%{_libdir}/mysql/mysql_config
install -m 0755 scriptstub ${RPM_BUILD_ROOT}%{_bindir}/mysql_config

rm -f ${RPM_BUILD_ROOT}%{_bindir}/comp_err
rm -f ${RPM_BUILD_ROOT}%{_mandir}/man1/comp_err.1*
rm -f ${RPM_BUILD_ROOT}%{_bindir}/make_win_binary_distribution
rm -f ${RPM_BUILD_ROOT}%{_bindir}/make_win_src_distribution
rm -f ${RPM_BUILD_ROOT}%{_mandir}/man1/make_win_bin_dist.1*
rm -f ${RPM_BUILD_ROOT}%{_mandir}/man1/make_win_src_distribution.1*
rm -f ${RPM_BUILD_ROOT}%{_libdir}/mysql/libmysqlclient*.la
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/binary-configure
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/make_binary_distribution
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/make_sharedlib_distribution
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/mi_test_all*
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/ndb-config-2-node.ini
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/mysql.server
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/mysqld_multi.server
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/MySQL-shared-compat.spec
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/*.plist
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/preinstall
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/postinstall
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/mysql-*.spec
rm -f ${RPM_BUILD_ROOT}%{_datadir}/mysql/mysql-log-rotate
rm -f ${RPM_BUILD_ROOT}%{_mandir}/man1/mysql-stress-test.pl.1*
rm -f ${RPM_BUILD_ROOT}%{_mandir}/man1/mysql-test-run.pl.1*
rm -f ${RPM_BUILD_ROOT}%{_mandir}/man1/ndbd.1*
rm -f ${RPM_BUILD_ROOT}%{_mandir}/man1/ndb_*.1*

mkdir -p $RPM_BUILD_ROOT/etc/ld.so.conf.d
echo "%{_libdir}/mysql" > $RPM_BUILD_ROOT/etc/ld.so.conf.d/%{name}-%{_arch}.conf

# copy additional docs into build tree so %%doc will find them
cp %{SOURCE7} README.mysql-license

%clean
rm -rf $RPM_BUILD_ROOT

%pre server
/usr/sbin/useradd -M -o -r -d /var/lib/mysql -s /bin/bash \
	-c "MySQL Server" -u 27 mysql > /dev/null 2>&1 || :

%post 
/sbin/install-info %{_infodir}/mysql.info.gz %{_infodir}/dir
/sbin/ldconfig

%post server
if [ $1 = 1 ]; then
    /sbin/chkconfig --add mysqld
fi
/bin/chmod 0755 /var/lib/mysql
/bin/touch /var/log/mysqld.log

%preun
if [ $1 = 0 ]; then
    /sbin/install-info --delete %{_infodir}/mysql.info.gz %{_infodir}/dir || :
fi

%preun server
if [ $1 = 0 ]; then
    /sbin/chkconfig --del mysqld
fi

%postun
if [ $1 = 0 ] ; then
    /sbin/ldconfig
fi


%postun server
if [ $1 -ge 1 ]; then
    /sbin/service mysqld condrestart >/dev/null 2>&1 || :
fi


%files
%defattr(-,root,root)
%doc README COPYING README.mysql-license

%{_bindir}/msql2mysql
%{_bindir}/mysql
%{_bindir}/mysql_config
%{_bindir}/mysql_find_rows
%{_bindir}/mysql_tableinfo
%{_bindir}/mysql_waitpid
%{_bindir}/mysqlaccess
%{_bindir}/mysqladmin
%{_bindir}/mysqlbinlog
%{_bindir}/mysqlcheck
%{_bindir}/mysqldump
%{_bindir}/mysqlimport
%{_bindir}/mysqlshow
%{_bindir}/my_print_defaults

%{_infodir}/*

%{_mandir}/man1/mysql.1*
%{_mandir}/man1/mysql_config.1*
%{_mandir}/man1/mysql_find_rows.1*
%{_mandir}/man1/mysql_tableinfo.1*
%{_mandir}/man1/mysql_waitpid.1*
%{_mandir}/man1/mysqlaccess.1*
%{_mandir}/man1/mysqladmin.1*
%{_mandir}/man1/mysqldump.1*
%{_mandir}/man1/mysqlshow.1*
%{_mandir}/man1/my_print_defaults.1*

%dir %{_libdir}/mysql
%{_libdir}/mysql/libmysqlclient*.so.*
%{_libdir}/mysql/mysqlbug
%{_libdir}/mysql/mysql_config
/etc/ld.so.conf.d/*

%dir %{_datadir}/mysql
%{_datadir}/mysql/english
%lang(cs) %{_datadir}/mysql/czech
%lang(da) %{_datadir}/mysql/danish
%lang(nl) %{_datadir}/mysql/dutch
%lang(et) %{_datadir}/mysql/estonian
%lang(fr) %{_datadir}/mysql/french
%lang(de) %{_datadir}/mysql/german
%lang(el) %{_datadir}/mysql/greek
%lang(hu) %{_datadir}/mysql/hungarian
%lang(it) %{_datadir}/mysql/italian
%lang(ja) %{_datadir}/mysql/japanese
%lang(ko) %{_datadir}/mysql/korean
%lang(no) %{_datadir}/mysql/norwegian
%lang(no) %{_datadir}/mysql/norwegian-ny
%lang(pl) %{_datadir}/mysql/polish
%lang(pt) %{_datadir}/mysql/portuguese
%lang(ro) %{_datadir}/mysql/romanian
%lang(ru) %{_datadir}/mysql/russian
%lang(sr) %{_datadir}/mysql/serbian
%lang(sk) %{_datadir}/mysql/slovak
%lang(es) %{_datadir}/mysql/spanish
%lang(sv) %{_datadir}/mysql/swedish
%lang(uk) %{_datadir}/mysql/ukrainian
%{_datadir}/mysql/charsets
%config(noreplace) /etc/my.cnf

%files server
%defattr(-,root,root)
%doc support-files/*.cnf

%{_bindir}/myisamchk
%{_bindir}/myisam_ftdump
%{_bindir}/myisamlog
%{_bindir}/myisampack
%{_bindir}/mysql_convert_table_format
%{_bindir}/mysql_explain_log
%{_bindir}/mysql_fix_extensions
%{_bindir}/mysql_fix_privilege_tables
%{_bindir}/mysql_install_db
%{_bindir}/mysql_secure_installation
%{_bindir}/mysql_setpermission
%{_bindir}/mysql_tzinfo_to_sql
%{_bindir}/mysql_upgrade
%{_bindir}/mysql_upgrade_shell
%{_bindir}/mysql_zap
%{_bindir}/mysqlbug
%{_bindir}/mysqldumpslow
%{_bindir}/mysqld_multi
%{_bindir}/mysqld_safe
%{_bindir}/mysqlhotcopy
%{_bindir}/mysqltestmanager
%{_bindir}/mysqltestmanager-pwgen
%{_bindir}/mysqltestmanagerc
%{_bindir}/mysqltest
%{_bindir}/innochecksum
%{_bindir}/perror
%{_bindir}/replace
%{_bindir}/resolve_stack_dump
%{_bindir}/resolveip

/usr/libexec/mysqld
/usr/libexec/mysqlmanager

%{_mandir}/man1/msql2mysql.1*
%{_mandir}/man1/myisamchk.1*
%{_mandir}/man1/myisamlog.1*
%{_mandir}/man1/myisampack.1*
%{_mandir}/man1/mysql_convert_table_format.1*
%{_mandir}/man1/myisam_ftdump.1*
%{_mandir}/man1/mysql.server.1*
%{_mandir}/man1/mysql_explain_log.1*
%{_mandir}/man1/mysql_fix_extensions.1*
%{_mandir}/man1/mysql_fix_privilege_tables.1*
%{_mandir}/man1/mysql_install_db.1*
%{_mandir}/man1/mysql_secure_installation.1*
%{_mandir}/man1/mysql_upgrade.1*
%{_mandir}/man1/mysql_zap.1*
%{_mandir}/man1/mysqlbug.1*
%{_mandir}/man1/mysqlbinlog.1*
%{_mandir}/man1/mysqlcheck.1*
%{_mandir}/man1/mysqldumpslow.1*
%{_mandir}/man1/mysqld_multi.1*
%{_mandir}/man1/mysqld_safe.1*
%{_mandir}/man1/mysqlhotcopy.1*
%{_mandir}/man1/mysqlimport.1*
%{_mandir}/man1/mysqlman.1*
%{_mandir}/man1/mysql_setpermission.1*
%{_mandir}/man1/mysqltest.1*
%{_mandir}/man1/innochecksum.1*
%{_mandir}/man1/perror.1*
%{_mandir}/man1/replace.1*
%{_mandir}/man1/resolve_stack_dump.1*
%{_mandir}/man1/resolveip.1*
%{_mandir}/man1/safe_mysqld.1*
%{_mandir}/man1/mysql_tzinfo_to_sql.1*
%{_mandir}/man8/mysqld.8*
%{_mandir}/man8/mysqlmanager.8*

%{_datadir}/mysql/errmsg.txt
%{_datadir}/mysql/fill_help_tables.sql
%{_datadir}/mysql/mysql_fix_privilege_tables.sql
%{_datadir}/mysql/mysql_system_tables.sql
%{_datadir}/mysql/mysql_system_tables_data.sql
%{_datadir}/mysql/mysql_test_data_timezone.sql
%{_datadir}/mysql/my-*.cnf
/etc/rc.d/init.d/mysqld
%attr(0755,mysql,mysql) %dir /var/run/mysqld
%attr(0755,mysql,mysql) %dir /var/lib/mysql
%attr(0640,mysql,mysql) %config(noreplace) %verify(not md5 size mtime) /var/log/mysqld.log

%files devel
%defattr(-,root,root)
/usr/include/mysql
%{_libdir}/mysql/*.a
%{_libdir}/mysql/libmysqlclient*.so

%files bench
%defattr(-,root,root)
%{_datadir}/sql-bench

%files test
%defattr(-,root,root)
%{_bindir}/mysql_client_test
%attr(-,mysql,mysql) %{_datadir}/mysql-test

%{_mandir}/man1/mysql_client_test.1*

%changelog
* Sat Feb  4 2012 Tom Lane <tgl@redhat.com> 5.0.95-1.el5_7.1
- Update to 5.0.95, to get the last upstream bugfixes in this release series
  including numerous CVEs announced in January 2012
Resolves: #787140

* Thu Apr 28 2011 Tom Lane <tgl@redhat.com> 5.0.77-4.el5_6.6
- Add fix for regression with input lines over 1MB (caused by fix for 658863)
Resolves: #700497
- Add fix for memory leak with DISTINCT, ORDER BY in subquery
Resolves: #692953

* Fri Dec  3 2010 Tom Lane <tgl@redhat.com> 5.0.77-4.5
- Add fix for crash during SHOW CREATE TABLE
Resolves: #659609
- Add fix for corruption of large BLOB values during dump/reload
Resolves: #658863

* Fri Oct 22 2010 Tom Lane <tgl@redhat.com> 5.0.77-4.4
- Add fixes for CVE-2010-3677, CVE-2010-3680, CVE-2010-3681, CVE-2010-3682,
  CVE-2010-3833, CVE-2010-3835, CVE-2010-3836, CVE-2010-3837, CVE-2010-3838,
  CVE-2010-3839, CVE-2010-3840
Resolves: #645642
- Backpatch strmov fix so that code can be tested on more recent platforms

* Thu May 20 2010 Tomas Hoger <thoger@redhat.com> 5.0.77-4.3
- Add fixes for CVE-2010-1626, CVE-2010-1848, CVE-2010-1850

* Fri Jan 29 2010 Tom Lane <tgl@redhat.com> 5.0.77-4.2
- Add fixes for CVE-2009-4019, CVE-2009-4028, CVE-2009-4030
Resolves: #556505
- Use non-expired certificates for SSL testing (upstream bug 50702)
- Emit explicit error message if user tries to build RPM as root
- Add comment suggesting disabling symbolic links in /etc/my.cnf

* Wed Dec 16 2009 Tom Lane <tgl@redhat.com> 5.0.77-4.1
- Add fix for server crash on comparison of dates to NAME_CONST
Resolves: #538731

* Thu Jul 16 2009 Tom Lane <tgl@redhat.com> 5.0.77-3
- Add fix for CVE-2009-2446 (format string vulnerability in COM_CREATE_DB and
  COM_DROP_DB processing)
Resolves: #512200

* Mon May 25 2009 Tom Lane <tgl@redhat.com> 5.0.77-2
- Back-port upstream fix for CVE-2008-4456 (mysql command line client XSS flaw)
Resolves: #502169

* Tue Apr  7 2009 Tom Lane <tgl@redhat.com> 5.0.77-1
- Update to MySQL 5.0.77, for numerous fixes described at
  http://dev.mysql.com/doc/refman/5.0/en/releasenotes-cs-5-0-77.html
  including low-priority security issues CVE-2008-2079, CVE-2008-3963
Resolves: #448487, #448534, #452824, #453156, #455619, #456875
Resolves: #457218, #462534, #470036, #476896, #479615
- Improve mysql.init to pass configured datadir to mysql_install_db,
  and to force user=mysql for both mysql_install_db and mysqld_safe.
Resolves: #450178
- Fix mysql.init to wait correctly when socket is not in default place
Resolves: #435494

* Wed Mar 26 2008 Tom Lane <tgl@redhat.com> 5.0.45-7
- Adjust thread stack requests to allow for platform-specific guard page size;
  necessary to prevent stack overrun on PPC with RHEL5's 64K page size.
Resolves: #435391
- Remove calendar-dependent queries from "view" test; necessary to get
  regression tests to pass after 2007.

* Thu Dec 13 2007 Tom Lane <tgl@redhat.com> 5.0.45-6
- Back-port upstream fixes for CVE-2007-5925, CVE-2007-5969, CVE-2007-6303.
Resolves: #422211

* Tue Nov 20 2007 Tom Lane <tgl@redhat.com> 5.0.45-1
- Update to MySQL 5.0.45
Resolves: #256501, #240813, #246309, #254012
Resolves: #280811, #316451, #349121, #367131
- Synchronize with current Fedora package, which is pretty well tested by now;
  see past bzs 245770, 241912, 233771, 221085, 223713, 203910, 193559, 199368

* Mon Aug 27 2007 Tom Lane <tgl@redhat.com> 5.0.22-3
- Fix CVE-2007-3780: remote DOS via bad password length byte
Resolves: #257681

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 5.0.22-2.1
- rebuild

* Sat Jun 10 2006 Tom Lane <tgl@redhat.com> 5.0.22-2
- Work around brew's tendency not to clean up failed builds completely,
  by adding code in mysql-testing.patch to kill leftover mysql daemons.

* Thu Jun  8 2006 Tom Lane <tgl@redhat.com> 5.0.22-1
- Update to MySQL 5.0.22 (fixes CVE-2006-2753)
- Install temporary workaround for gcc bug on s390x (bz #193912)

* Tue May  2 2006 Tom Lane <tgl@redhat.com> 5.0.21-2
- Fix bogus perl Requires for mysql-test

* Mon May  1 2006 Tom Lane <tgl@redhat.com> 5.0.21-1
- Update to MySQL 5.0.21

* Mon Mar 27 2006 Tom Lane <tgl@redhat.com> 5.0.18-4
- Modify multilib header hack to not break non-RH arches, per bug #181335
- Remove logrotate script, per bug #180639.
- Add a new mysql-test RPM to carry the regression test files;
  hack up test scripts as needed to make them run in /usr/share/mysql-test.

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 5.0.18-2.1
- bump again for double-long bug on ppc(64)

* Thu Feb  9 2006 Tom Lane <tgl@redhat.com> 5.0.18-2
- err-log option has been renamed to log-error, fix my.cnf and initscript

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 5.0.18-1.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Thu Jan  5 2006 Tom Lane <tgl@redhat.com> 5.0.18-1
- Update to MySQL 5.0.18

* Thu Dec 15 2005 Tom Lane <tgl@redhat.com> 5.0.16-4
- fix my_config.h for ppc platforms

* Thu Dec 15 2005 Tom Lane <tgl@redhat.com> 5.0.16-3
- my_config.h needs to guard against 64-bit platforms that also define the
  32-bit symbol

* Wed Dec 14 2005 Tom Lane <tgl@redhat.com> 5.0.16-2
- oops, looks like we want uname -i not uname -m

* Mon Dec 12 2005 Tom Lane <tgl@redhat.com> 5.0.16-1
- Update to MySQL 5.0.16
- Add EXCEPTIONS-CLIENT license info to the shipped documentation
- Make my_config.h architecture-independent for multilib installs;
  put the original my_config.h into my_config_$ARCH.h
- Add -fwrapv to CFLAGS so that gcc 4.1 doesn't break it

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Mon Nov 14 2005 Tom Lane <tgl@redhat.com> 5.0.15-3
- Make stop script wait for daemon process to disappear (bz#172426)

* Wed Nov  9 2005 Tom Lane <tgl@redhat.com> 5.0.15-2
- Rebuild due to openssl library update.

* Thu Nov  3 2005 Tom Lane <tgl@redhat.com> 5.0.15-1
- Update to MySQL 5.0.15 (scratch build for now)

* Wed Oct  5 2005 Tom Lane <tgl@redhat.com> 4.1.14-1
- Update to MySQL 4.1.14

* Tue Aug 23 2005 Tom Lane <tgl@redhat.com> 4.1.12-3
- Use politically correct patch name.

* Tue Jul 12 2005 Tom Lane <tgl@redhat.com> 4.1.12-2
- Fix buffer overflow newly exposed in isam code; it's the same issue
  previously found in myisam, and not very exciting, but I'm tired of
  seeing build warnings.

* Mon Jul 11 2005 Tom Lane <tgl@redhat.com> 4.1.12-1
- Update to MySQL 4.1.12 (includes a fix for bz#158688, bz#158689)
- Extend mysql-test-ssl.patch to solve rpl_openssl test failure (bz#155850)
- Update mysql-lock-ssl.patch to match the upstream committed version
- Add --with-isam to re-enable the old ISAM table type, per bz#159262
- Add dependency on openssl-devel per bz#159569
- Remove manual.txt, as upstream decided not to ship it anymore;
  it was redundant with the mysql.info file anyway.

* Mon May  9 2005 Tom Lane <tgl@redhat.com> 4.1.11-4
- Include proper locking for OpenSSL in the server, per bz#155850

* Mon Apr 25 2005 Tom Lane <tgl@redhat.com> 4.1.11-3
- Enable openssl tests during build, per bz#155850
- Might as well turn on --disable-dependency-tracking

* Fri Apr  8 2005 Tom Lane <tgl@redhat.com> 4.1.11-2
- Avoid dependency on <asm/atomic.h>, cause it won't build anymore on ia64.
  This is probably a cleaner solution for bz#143537, too.

* Thu Apr  7 2005 Tom Lane <tgl@redhat.com> 4.1.11-1
- Update to MySQL 4.1.11 to fix bz#152911 as well as other issues
- Move perl-DBI, perl-DBD-MySQL dependencies to server package (bz#154123)
- Override configure thread library test to suppress HAVE_LINUXTHREADS check
- Fix BDB failure on s390x (bz#143537)
- At last we can enable "make test" on all arches

* Fri Mar 11 2005 Tom Lane <tgl@redhat.com> 4.1.10a-1
- Update to MySQL 4.1.10a to fix security vulnerabilities (bz#150868,
  for CAN-2005-0711, and bz#150871 for CAN-2005-0709, CAN-2005-0710).

* Sun Mar  6 2005 Tom Lane <tgl@redhat.com> 4.1.10-3
- Fix package Requires: interdependencies.

* Sat Mar  5 2005 Tom Lane <tgl@redhat.com> 4.1.10-2
- Need -fno-strict-aliasing in at least one place, probably more.
- Work around some C spec violations in mysql.

* Fri Feb 18 2005 Tom Lane <tgl@redhat.com> 4.1.10-1
- Update to MySQL 4.1.10.

* Sat Jan 15 2005 Tom Lane <tgl@redhat.com> 4.1.9-1
- Update to MySQL 4.1.9.

* Wed Jan 12 2005 Tom Lane <tgl@redhat.com> 4.1.7-10
- Don't assume /etc/my.cnf will specify pid-file (bz#143724)

* Wed Jan 12 2005 Tim Waugh <twaugh@redhat.com> 4.1.7-9
- Rebuilt for new readline.

* Tue Dec 21 2004 Tom Lane <tgl@redhat.com> 4.1.7-8
- Run make test on all archs except s390x (which seems to have a bdb issue)

* Mon Dec 13 2004 Tom Lane <tgl@redhat.com> 4.1.7-7
- Suppress someone's silly idea that libtool overhead can be skipped

* Sun Dec 12 2004 Tom Lane <tgl@redhat.com> 4.1.7-6
- Fix init script to not need a valid username for startup check (bz#142328)
- Fix init script to honor settings appearing in /etc/my.cnf (bz#76051)
- Enable SSL (bz#142032)

* Thu Dec  2 2004 Tom Lane <tgl@redhat.com> 4.1.7-5
- Add a restorecon to keep the mysql.log file in the right context (bz#143887)

* Tue Nov 23 2004 Tom Lane <tgl@redhat.com> 4.1.7-4
- Turn off old_passwords in default /etc/my.cnf file, for better compatibility
  with mysql 3.x clients (per suggestion from Joe Orton).

* Fri Oct 29 2004 Tom Lane <tgl@redhat.com> 4.1.7-3
- Handle ldconfig more cleanly (put a file in /etc/ld.so.conf.d/).

* Thu Oct 28 2004 Tom Lane <tgl@redhat.com> 4.1.7-2
- rebuild in devel branch

* Wed Oct 27 2004 Tom Lane <tgl@redhat.com> 4.1.7-1
- Update to MySQL 4.1.x.

* Tue Oct 12 2004 Tom Lane <tgl@redhat.com> 3.23.58-13
- fix security issues CAN-2004-0835, CAN-2004-0836, CAN-2004-0837
  (bugs #135372, 135375, 135387)
- fix privilege escalation on GRANT ALL ON `Foo\_Bar` (CAN-2004-0957)

* Wed Oct 06 2004 Tom Lane <tgl@redhat.com> 3.23.58-12
- fix multilib problem with mysqlbug and mysql_config
- adjust chkconfig priority per bug #128852
- remove bogus quoting per bug #129409 (MySQL 4.0 has done likewise)
- add sleep to mysql.init restart(); may or may not fix bug #133993

* Tue Oct 05 2004 Tom Lane <tgl@redhat.com> 3.23.58-11
- fix low-priority security issues CAN-2004-0388, CAN-2004-0381, CAN-2004-0457
  (bugs #119442, 125991, 130347, 130348)
- fix bug with dropping databases under recent kernels (bug #124352)

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com> 3.23.58-10
- rebuilt

* Sat Apr 17 2004 Warren Togami <wtogami@redhat.com> 3.23.58-9
- remove redundant INSTALL-SOURCE, manual.*
- compress manual.txt.bz2
- BR time

* Tue Mar 16 2004 Tom Lane <tgl@redhat.com> 3.23.58-8
- repair logfile attributes in %%files, per bug #102190
- repair quoting problem in mysqlhotcopy, per bug #112693
- repair missing flush in mysql_setpermission, per bug #113960
- repair broken error message printf, per bug #115165
- delete mysql user during uninstall, per bug #117017
- rebuilt

* Tue Mar 02 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Tue Feb 24 2004 Tom Lane <tgl@redhat.com>
- fix chown syntax in mysql.init
- rebuild

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Tue Nov 18 2003 Kim Ho <kho@redhat.com> 3.23.58-5
- update mysql.init to use anonymous user (UNKNOWN_MYSQL_USER) for
  pinging mysql server (#108779)

* Mon Oct 27 2003 Kim Ho <kho@redhat.com> 3.23.58-4
- update mysql.init to wait (max 10 seconds) for mysql server to 
  start (#58732)

* Mon Oct 27 2003 Patrick Macdonald <patrickm@redhat.com> 3.23.58-3
- re-enable Berkeley DB support (#106832)
- re-enable ia64 testing

* Fri Sep 19 2003 Patrick Macdonald <patrickm@redhat.com> 3.23.58-2
- rebuilt

* Mon Sep 15 2003 Patrick Macdonald <patrickm@redhat.com> 3.23.58-1
- upgrade to 3.23.58 for security fix

* Tue Aug 26 2003 Patrick Macdonald <patrickm@redhat.com> 3.23.57-2
- rebuilt

* Wed Jul 02 2003 Patrick Macdonald <patrickm@redhat.com> 3.23.57-1
- revert to prior version of MySQL due to license incompatibilities 
  with packages that link against the client.  The MySQL folks are
  looking into the issue.

* Wed Jun 18 2003 Patrick Macdonald <patrickm@redhat.com> 4.0.13-4
- restrict test on ia64 (temporary)

* Wed Jun 04 2003 Elliot Lee <sopwith@redhat.com> 4.0.13-3
- rebuilt

* Thu May 29 2003 Patrick Macdonald <patrickm@redhat.com> 4.0.13-2
- fix filter-requires-mysql.sh with less restrictive for mysql-bench 

* Wed May 28 2003 Patrick Macdonald <patrickm@redhat.com> 4.0.13-1
- update for MySQL 4.0
- back-level shared libraries available in mysqlclient10 package

* Fri May 09 2003 Patrick Macdonald <patrickm@redhat.com> 3.23.56-2
- add sql-bench package (#90110) 

* Wed Mar 19 2003 Patrick Macdonald <patrickm@redhat.com> 3.23.56-1
- upgrade to 3.23.56 for security fixes
- remove patch for double-free (included in 3.23.56) 

* Tue Feb 18 2003 Patrick Macdonald <patrickm@redhat.com> 3.23.54a-11
- enable thread safe client
- add patch for double free fix

* Wed Jan 22 2003 Tim Powers <timp@redhat.com>
- rebuilt

* Mon Jan 13 2003 Karsten Hopp <karsten@redhat.de> 3.23.54a-9
- disable checks on s390x

* Sat Jan  4 2003 Jeff Johnson <jbj@redhat.com> 3.23.54a-8
- use internal dep generator.

* Wed Jan  1 2003 Bill Nottingham <notting@redhat.com> 3.23.54a-7
- fix mysql_config on hammer

* Sun Dec 22 2002 Tim Powers <timp@redhat.com> 3.23.54a-6
- don't use rpms internal dep generator

* Tue Dec 17 2002 Elliot Lee <sopwith@redhat.com> 3.23.54a-5
- Push it into the build system

* Mon Dec 16 2002 Joe Orton <jorton@redhat.com> 3.23.54a-4
- upgrade to 3.23.54a for safe_mysqld fix

* Thu Dec 12 2002 Joe Orton <jorton@redhat.com> 3.23.54-3
- upgrade to 3.23.54 for latest security fixes

* Tue Nov 19 2002 Jakub Jelinek <jakub@redhat.com> 3.23.52-5
- Always include <errno.h> for errno
- Remove unpackaged files

* Tue Nov 12 2002 Florian La Roche <Florian.LaRoche@redhat.de>
- do not prereq userdel, not used at all

* Mon Sep  9 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.52-4
- Use %%{_libdir}
- Add patch for x86-64

* Wed Sep  4 2002 Jakub Jelinek <jakub@redhat.com> 3.23.52-3
- rebuilt with gcc-3.2-7

* Thu Aug 29 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.52-2
- Add --enable-local-infile to configure - a new option
  which doesn't default to the old behaviour (#72885)

* Fri Aug 23 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.52-1
- 3.23.52. Fixes a minor security problem, various bugfixes.

* Sat Aug 10 2002 Elliot Lee <sopwith@redhat.com> 3.23.51-5
- rebuilt with gcc-3.2 (we hope)

* Mon Jul 22 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.51-4
- rebuild

* Thu Jul 18 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.51-3
- Fix #63543 and #63542 

* Thu Jul 11 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.51-2
- Turn off bdb on PPC(#68591)
- Turn off the assembly optimizations, for safety. 

* Wed Jun 26 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.51-1
- Work around annoying auto* thinking this is a crosscompile
- 3.23.51

* Fri Jun 21 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Mon Jun 10 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.50-2
- Add dependency on perl-DBI and perl-DBD-MySQL (#66349)

* Thu May 30 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.50-1
- 3.23.50

* Thu May 23 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Mon May 13 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.49-4
- Rebuild
- Don't set CXX to gcc, it doesn't work anymore
- Exclude Alpha

* Mon Apr  8 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.49-3
- Add the various .cnf examples as doc files to mysql-server (#60349)
- Don't include manual.ps, it's just 200 bytes with a URL inside (#60349)
- Don't include random files in /usr/share/mysql (#60349)
- langify (#60349)

* Thu Feb 21 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.49-2
- Rebuild

* Sun Feb 17 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.49-1
- 3.23.49

* Thu Feb 14 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.48-2
- work around perl dependency bug.

* Mon Feb 11 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.48-1
- 3.23.48

* Thu Jan 17 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.47-4
- Use kill, not mysqladmin, to flush logs and shut down. Thus, 
  an admin password can be set with no problems.
- Remove reload from init script

* Wed Jan 16 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.47-3
- remove db3-devel from buildrequires, 
  MySQL has had its own bundled copy since the mid thirties

* Sun Jan  6 2002 Trond Eivind Glomsrød <teg@redhat.com> 3.23.47-1
- 3.23.47
- Don't build for alpha, toolchain immature.

* Mon Dec  3 2001 Trond Eivind Glomsrød <teg@redhat.com> 3.23.46-1
- 3.23.46
- use -fno-rtti and -fno-exceptions, and set CXX to increase stability. 
  Recommended by mysql developers.

* Sun Nov 25 2001 Trond Eivind Glomsrød <teg@redhat.com> 3.23.45-1
- 3.23.45

* Wed Nov 14 2001 Trond Eivind Glomsrød <teg@redhat.com> 3.23.44-2
- centralize definition of datadir in the initscript (#55873)

* Fri Nov  2 2001 Trond Eivind Glomsrød <teg@redhat.com> 3.23.44-1
- 3.23.44

* Thu Oct  4 2001 Trond Eivind Glomsrød <teg@redhat.com> 3.23.43-1
- 3.23.43

* Mon Sep 10 2001 Trond Eivind Glomsrød <teg@redhat.com> 3.23.42-1
- 3.23.42
- reenable innodb

* Tue Aug 14 2001 Trond Eivind Glomsrød <teg@redhat.com> 3.23.41-1
- 3.23.41 bugfix release
- disable innodb, to avoid the broken updates
- Use "mysqladmin flush_logs" instead of kill -HUP in logrotate 
  script (#51711)

* Sat Jul 21 2001 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.40, bugfix release
- Add zlib-devel to buildrequires:

* Fri Jul 20 2001 Trond Eivind Glomsrød <teg@redhat.com>
- BuildRequires-tweaking

* Thu Jun 28 2001 Trond Eivind Glomsrød <teg@redhat.com>
- Reenable test, but don't run them for s390, s390x or ia64
- Make /etc/my.cnf config(noplace). Same for /etc/logrotate.d/mysqld

* Thu Jun 14 2001 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.29
- enable innodb
- enable assembly again
- disable tests for now...

* Tue May 15 2001 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.38
- Don't use BDB on Alpha - no fast mutexes

* Tue Apr 24 2001 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.37
- Add _GNU_SOURCE to the compile flags

* Wed Mar 28 2001 Trond Eivind Glomsrød <teg@redhat.com>
- Make it obsolete our 6.2 PowerTools packages
- 3.23.36 bugfix release - fixes some security issues
  which didn't apply to our standard configuration
- Make "make test" part of the build process, except on IA64
  (it fails there)

* Tue Mar 20 2001 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.35 bugfix release
- Don't delete the mysql user on uninstall

* Tue Mar 13 2001 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.34a bugfix release

* Wed Feb  7 2001 Trond Eivind Glomsrød <teg@redhat.com>
- added readline-devel to BuildRequires:

* Tue Feb  6 2001 Trond Eivind Glomsrød <teg@redhat.com>
- small i18n-fixes to initscript (action needs $)

* Tue Jan 30 2001 Trond Eivind Glomsrød <teg@redhat.com>
- make it shut down and rotate logs without using mysqladmin 
  (from #24909)

* Mon Jan 29 2001 Trond Eivind Glomsrød <teg@redhat.com>
- conflict with "MySQL"

* Tue Jan 23 2001 Trond Eivind Glomsrød <teg@redhat.com>
- improve gettextizing

* Mon Jan 22 2001 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.32
- fix logrotate script (#24589)

* Wed Jan 17 2001 Trond Eivind Glomsrød <teg@redhat.com>
- gettextize
- move the items in Requires(post): to Requires: in preparation
  for an errata for 7.0 when 3.23.31 is released
- 3.23.31

* Tue Jan 16 2001 Trond Eivind Glomsrød <teg@redhat.com>
- add the log file to the rpm database, and make it 0640
  (#24116)
- as above in logrotate script
- changes to the init sequence - put most of the data
  in /etc/my.cnf instead of hardcoding in the init script
- use /var/run/mysqld/mysqld.pid instead of 
  /var/run/mysqld/pid
- use standard safe_mysqld
- shut down cleaner

* Mon Jan 08 2001 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.30
- do an explicit chmod on /var/lib/mysql in post, to avoid 
  any problems with broken permissons. There is a report
  of rm not changing this on its own (#22989)

* Mon Jan 01 2001 Trond Eivind Glomsrød <teg@redhat.com>
- bzipped source
- changed from 85 to 78 in startup, so it starts before
  apache (which can use modules requiring mysql)

* Wed Dec 27 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.29a

* Tue Dec 19 2000 Trond Eivind Glomsrød <teg@redhat.com>
- add requirement for new libstdc++, build for errata

* Mon Dec 18 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.29

* Mon Nov 27 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.28 (gamma)
- remove old patches, as they are now upstreamed

* Thu Nov 14 2000 Trond Eivind Glomsrød <teg@redhat.com>
- Add a requirement for a new glibc (#20735)
- build on IA64

* Wed Nov  1 2000 Trond Eivind Glomsrød <teg@redhat.com>
- disable more assembly

* Wed Nov  1 2000 Jakub Jelinek <jakub@redhat.com>
- fix mysql on SPARC (#20124)

* Tue Oct 31 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.27

* Wed Oct 25 2000 Trond Eivind Glomsrød <teg@redhat.com>
- add patch for fixing bogus aliasing in mysql from Jakub,
  which should fix #18905 and #18620

* Mon Oct 23 2000 Trond Eivind Glomsrød <teg@redhat.com>
- check for negative niceness values, and negate it
  if present (#17899)
- redefine optflags on IA32 FTTB

* Wed Oct 18 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.26, which among other fixes now uses mkstemp()
  instead of tempnam().
- revert changes made yesterday, the problem is now
  isolated
 
* Tue Oct 17 2000 Trond Eivind Glomsrød <teg@redhat.com>
- use the compat C++ compiler FTTB. Argh.
- add requirement of ncurses4 (see above)

* Sun Oct 01 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.25
- fix shutdown problem (#17956)

* Tue Sep 26 2000 Trond Eivind Glomsrød <teg@redhat.com>
- Don't try to include no-longer-existing PUBLIC file
  as doc (#17532)

* Thu Sep 12 2000 Trond Eivind Glomsrød <teg@redhat.com>
- rename config file to /etc/my.cnf, which is what
  mysqld wants... doh. (#17432)
- include a changed safe_mysqld, so the pid file option
  works. 
- make mysql dir world readable to they can access the 
  mysql socket. (#17432)
- 3.23.24

* Wed Sep 06 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.23

* Sun Aug 27 2000 Trond Eivind Glomsrød <teg@redhat.com>
- Add "|| :" to condrestart to avoid non-zero exit code

* Thu Aug 24 2000 Trond Eivind Glomsrød <teg@redhat.com>
- it's mysql.com, not mysql.org and use correct path to 
  source (#16830)

* Wed Aug 16 2000 Trond Eivind Glomsrød <teg@redhat.com>
- source file from /etc/rc.d, not /etc/rd.d. Doh.

* Sun Aug 13 2000 Trond Eivind Glomsrød <teg@redhat.com>
- don't run ldconfig -n, it doesn't update ld.so.cache
  (#16034)
- include some missing binaries
- use safe_mysqld to start the server (request from
  mysql developers)

* Sat Aug 05 2000 Bill Nottingham <notting@redhat.com>
- condrestart fixes

* Mon Aug 01 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.22. Disable the old patches, they're now in.

* Thu Jul 27 2000 Trond Eivind Glomsrød <teg@redhat.com>
- bugfixes in the initscript
- move the .so link to the devel package

* Wed Jul 19 2000 Trond Eivind Glomsrød <teg@redhat.com>
- rebuild due to glibc changes

* Tue Jul 18 2000 Trond Eivind Glomsrød <teg@redhat.com>
- disable compiler patch
- don't include info directory file

* Mon Jul 17 2000 Trond Eivind Glomsrød <teg@redhat.com>
- move back to /etc/rc.d/init.d

* Fri Jul 14 2000 Trond Eivind Glomsrød <teg@redhat.com>
- more cleanups in initscript

* Thu Jul 13 2000 Trond Eivind Glomsrød <teg@redhat.com>
- add a patch to work around compiler bug 
  (from monty@mysql.com) 

* Wed Jul 12 2000 Trond Eivind Glomsrød <teg@redhat.com>
- don't build the SQL daemon statically (glibc problems)
- fix the logrotate script - only flush log if mysql
  is running
- change the reloading procedure 
- remove icon - glint is obsolete a long time ago

* Wed Jul 12 2000 Prospector <bugzilla@redhat.com>
- automatic rebuild

* Mon Jul 10 2000 Trond Eivind Glomsrød <teg@redhat.com>
- try the new compiler again
- build the SQL daemon statically
- add compile time support for complex charsets
- enable assembler
- more cleanups in initscript

* Sun Jul 09 2000 Trond Eivind Glomsrød <teg@redhat.com>
- use old C++ compiler
- Exclusivearch x86

* Sat Jul 08 2000 Trond Eivind Glomsrød <teg@redhat.com>
- move .so files to devel package
- more cleanups
- exclude sparc for now

* Wed Jul 05 2000 Trond Eivind Glomsrød <teg@redhat.com>
- 3.23.21
- remove file from /etc/sysconfig
- Fix initscript a bit - initialization of databases doesn't
  work yet
- specify the correct licenses
- include a /etc/my.conf (empty, FTTB)
- add conditional restart to spec file

* Tue Jul  2 2000 Jakub Jelinek <jakub@redhat.com>
- Rebuild with new C++

* Fri Jun 30 2000 Trond Eivind Glomsrød <teg@redhat.com>
- update to 3.23.20
- use %%configure, %%makeinstall, %%{_tmppath}, %%{_mandir},
  %%{_infodir}, /etc/init.d
- remove the bench package
- change some of the descriptions a little bit
- fix the init script
- some compile fixes
- specify mysql user
- use mysql uid 27 (postgresql is 26)
- don't build on ia64

* Sat Feb 26 2000 Jos Vos <jos@xos.nl>
- Version 3.22.32 release XOS.1 for LinuX/OS 1.8.0
- Upgrade from version 3.22.27 to 3.22.32.
- Do "make install" instead of "make install-strip", because "install -s"
  now appears to fail on various scripts.  Afterwards, strip manually.
- Reorganize subpackages, according to common Red Hat packages: the client
  program and shared library become the base package and the server and
  some accompanying files are now in a separate server package.  The
  server package implicitly requires the base package (shared library),
  but we have added a manual require tag anyway (because of the shared
  config file, and more).
- Rename the mysql-benchmark subpackage to mysql-bench.

* Mon Jan 31 2000 Jos Vos <jos@xos.nl>
- Version 3.22.27 release XOS.2 for LinuX/OS 1.7.1
- Add post(un)install scripts for updating ld.so.conf (client subpackage).

* Sun Nov 21 1999 Jos Vos <jos@xos.nl>
- Version 3.22.27 release XOS.1 for LinuX/OS 1.7.0
- Initial version.
- Some ideas borrowed from Red Hat Powertools 6.1, although this spec
  file is a full rewrite from scratch.
