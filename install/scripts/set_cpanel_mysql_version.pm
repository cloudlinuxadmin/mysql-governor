#!/bin/sh
eval 'if [ -x /usr/local/cpanel/3rdparty/bin/perl ]; then exec /usr/local/cpanel/3rdparty/bin/perl -x -- $0 ${1+"$@"}; else exec /usr/bin/perl -x $0 ${1+"$@"}; fi;'
if 0;

#!/usr/bin/perl

BEGIN { unshift @INC, '/usr/local/cpanel'; }
use strict;
use Whostmgr::Mysql::Upgrade ();

my ($new_version) = @ARGV;

Whostmgr::Mysql::Upgrade::set_mysql_version($new_version);
