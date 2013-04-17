#!/bin/bash

if [ -e /usr/local/cpanel/cpanel ]; then
        if [ -e /usr/local/cpanel/scripts/update_local_rpm_versions ]; then
    	    rm -f /etc/mysqlupdisable
    	    sed -i "/MYSQLUP=never/d" /etc/cpupdate.conf
        fi
fi




