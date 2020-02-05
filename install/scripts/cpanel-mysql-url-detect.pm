#!/bin/sh
eval 'if [ -x /usr/local/cpanel/3rdparty/bin/perl ]; then exec /usr/local/cpanel/3rdparty/bin/perl -x -- $0 ${1+"$@"}; else exec /usr/bin/perl -x $0 ${1+"$@"}; fi;'
  if 0;

#!/usr/bin/perl
# cpanel - scripts/check_cpanel_rpms              Copyright(c) 2015 cPanel, Inc.
#                                                           All rights Reserved.
# copyright@cpanel.net                                         http://cpanel.net
# This code is subject to the cPanel license. Unauthorized copying is prohibited

package scripts::check_cpanel_rpms;

# This script will handle repairing/listing broken RPMs
# -
# Q: What is a broken aka altered RPM?
# A: Any files output by a rpm -vV RPM_PACKAGE_NAME that are listed to have a different MD5 sum or permission change indicate a broken RPM.

use strict;
use warnings;

BEGIN {
    unshift @INC, '/usr/local/cpanel';
}

use Cpanel::CleanINC            ();
use Cpanel::Usage               ();
use Cpanel::Update::Logger      ();
use Cpanel::RPM::Versions::File ();
use Cpanel::Sys::Hostname       ();
use Cpanel::TempFile            ();

my ($name, $release) = @ARGV;

if (not defined $name) {
  print "";
  exit(1);
}

if (not defined $release) {
  print "";
  exit(1);
}

my $logger = Cpanel::Update::Logger->new( { 'stdout' => 0, 'log_level' => 'info' } );

my %directory_options = ();

my $v;
my $targets = "MySQL50,MySQL51,MySQL55,MySQL56,MariaDB,MariaDB100,MariaDB101,MariaDB102,MariaDB103,MariaDB104";
if ($targets) {
    my @targets = split( /\s*,\s*/, $targets );
    $v = Cpanel::RPM::Versions::File->new( { 'only_targets' => \@targets, logger => $logger, %directory_options } );
}
else {
    $v = Cpanel::RPM::Versions::File->new( { logger => $logger, %directory_options } );
}

print $v->url($name, $release);