#!/bin/sh
eval 'if [ -x /usr/local/cpanel/3rdparty/bin/perl ]; then exec /usr/local/cpanel/3rdparty/bin/perl -x -- $0 ${1+"$@"}; else exec /usr/bin/perl -x $0 ${1+"$@"}; fi;'
if 0;

#!/usr/bin/perl

BEGIN { unshift @INC, '/usr/local/cpanel', '/scripts'; }

my $pckg_name = 'Cpanel';
eval "use " . $pckg_name . ";";
use strict;

eval "use " .$pckg_name . "::SysPkgs          ();";
if ($@){
    $pckg_name = 'cPScript';
    eval "use " .$pckg_name . "::SysPkgs       ();";
}

#eval "use " .$pckg_name . "::SysPkgs              ();";
eval "use  " .$pckg_name . "::Sys 	           ();";
eval "use  " .$pckg_name . "::OSSys                ();";
eval "use  " .$pckg_name . "::HttpRequest          ();";
eval "use  " .$pckg_name . "::Config::LoadCpConf   ();";
eval "use  " .$pckg_name . "::RpmUtils             ();";
eval "use  " .$pckg_name . "::FileUtils::TouchFile ();";

my $mysqlTypeFileSet="/usr/share/lve/dbgovernor/mysql.type";
my $cPanelVersion=`/usr/local/cpanel/cpanel -V | cut -d'.' -f1`;
chomp $cPanelVersion;
my $cPanelsubVersion=`/usr/local/cpanel/cpanel -V | cut -d'.' -f2`;
chomp $cPanelsubVersion;

my $force   = 1;                                                                                                                                             
while ( $#ARGV != -1 ) {                                                                                                                                     
    if ( $ARGV[0] =~ m/^\-\-/ ) {                                                                                                                            
        my $arg = shift @ARGV;                                                                                                                               
        $arg =~ s/^\-\-//g;                                                                                                                                  
        $arg = lc $arg;                                                                                                                                      
        if ( $arg eq 'force' )   { $force   = 1; }                                                                                                           
    }                                                                                                                                                        
    else {                                                                                                                                                   
        last;                                                                                                                                                
    }                                                                                                                                                        
}   

my $httpClient = eval $pckg_name . "::HttpRequest->new( 'hideOutput' => 0 );";

my ( $system, $nodename, $release, $version, $machine ) = eval $pckg_name . "::OSSys::uname();";
my $arch = $machine;
if ( $machine =~ /i.86/ ) {
    $arch = 'i386';
}

my %CPCONF =  eval $pckg_name . "::Config::LoadCpConf::loadcpconf();";

# Default to 5.5 if mysql-version is unset
if (   !exists $CPCONF{'mysql-version'}
    || !defined $CPCONF{'mysql-version'}
    || $CPCONF{'mysql-version'} eq ''
    || $CPCONF{'mysql-version'} eq '3' ) {
    $CPCONF{'mysql-version'} = '5.5';
}

my $updated = 0;
my $url = 'http://repo.cloudlinux.com/cloudlinux';
my $baseurl    = $url . '/sources/cpanel/cl';
my $cPPkg      =  eval $pckg_name . "::cPPkgs->new( 'MySQL', '$baseurl' );";

my $sql_version = $CPCONF{'mysql-version'};
my $sql_version_2 = $sql_version;

if ($sql_version_2=="5.0"){
    $sql_version_2="mysql50";
}
if ($sql_version_2=="5.1"){
    $sql_version_2="mysql51";
}
if ($sql_version_2=="5.5"){
    $sql_version_2="mysql55";
}
if ($sql_version_2=="5.6"){
    $sql_version_2="mysql56";
}

if ($sql_version_2=="5.7"){
    $sql_version_2="mysql57";
}

if ($sql_version_2=="8.0"){
    $sql_version_2="mysql80";
}

if ($sql_version_2=="10.0"){
    $sql_version_2="mariadb100";
}

if ($sql_version_2=="10.1"){
    $sql_version_2="mariadb101";
}

if ($sql_version_2=="10.2"){
    $sql_version_2="mariadb102";
}

if ($sql_version_2=="10.3"){
    $sql_version_2="mariadb103";
}

if ($sql_version_2=="10.4"){
    $sql_version_2="mariadb104";
}

if ($sql_version_2=="10.5"){
    $sql_version_2="mariadb105";
}

if ($sql_version_2=="10.6"){
    $sql_version_2="mariadb106";
}

print "$sql_version_2";


