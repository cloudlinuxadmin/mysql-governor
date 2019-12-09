# Jailkit
# configure.ac - the autoconf file
#
#Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 Olivier Sessink
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions 
#are met:
#  * Redistributions of source code must retain the above copyright 
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above 
#    copyright notice, this list of conditions and the following 
#    disclaimer in the documentation and/or other materials provided 
#    with the distribution.
#  * The names of its contributors may not be used to endorse or 
#    promote products derived from this software without specific 
#    prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
#"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
#LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
#FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE 
#COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
#INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
#BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
#LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
#ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
#POSSIBILITY OF SUCH DAMAGE.
#
#

AC_INIT([governor],[0.6],[http://www.cloudlinux.com])

AC_SUBST([PACKAGE], AC_PACKAGE_NAME)
AC_DEFINE_UNQUOTED([PACKAGE], "AC_PACKAGE_NAME", [The package name.])
AC_SUBST([VERSION], AC_PACKAGE_VERSION)
AC_DEFINE_UNQUOTED([VERSION], "AC_PACKAGE_VERSION", [The package version.])

AC_PREFIX_DEFAULT([/usr])

AC_GNU_SOURCE

AC_PROG_CC
AC_ISC_POSIX
AC_C_INLINE
AC_PROG_INSTALL

if test "$CC" = "gcc" ; then
	CFLAGS="$CFLAGS -Wall -pipe"
fi

dnl ************************
dnl Check for standard headers
dnl ************************

AC_HEADER_STDC

dnl you should maybe add AC_ARG_VAR for every AC_PATH_PROG to allow users
dnl to specify the binary path if it is not in PATH
AC_ARG_VAR(
	[PYTHONINTERPRETER],
	[The `python' binary with path. Use it to define or override the location of `python'.]
)
AC_PATH_PROG([PYTHONINTERPRETER], [python], [no])
if test "x$PYTHONINTERPRETER" = "xno" ; then
	AC_MSG_ERROR([python not found please install python])
fi
AC_SUBST(PYTHONINTERPRETER)
AC_MSG_CHECKING([for up to date python])
echo -n "checking for up to date python... "
if /opt/alt/python27/bin/python2.7 -c 'i=1;i+=1' >/dev/null 2>&1 ; then
	AC_MSG_RESULT([ok])
else
	AC_MSG_RESULT([failed])
	AC_MSG_ERROR([your python version is too old, please install python 2 or newer])
fi

AC_ARG_VAR(
	[PROCMAILPATH],
	[The `procmail' binary with path. Use it to define or override the location of `procmail'.]
)
AC_PATH_PROG([PROCMAILPATH], [procmail], [no])
if test "x$PROCMAILPATH" != "xno" ; then
	AC_DEFINE_UNQUOTED([PROCMAILPATH], "$PROCMAILPATH", [The procmail path.])
	AC_SUBST([HAVEPROCMAIL_TRUE], [])
else
	AC_SUBST([HAVEPROCMAIL_TRUE], [#])
fi

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
