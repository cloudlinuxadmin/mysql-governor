#!/bin/bash

function getMYSQLUP {
    if [ -e /etc/cpupdate.conf ]; then
        cp /etc/cpupdate.conf /etc/cpupdate.conf.governor
        is_MYSQLUP=`grep MYSQLUP /etc/cpupdate.conf`
        if [ -n "$is_MYSQLUP" ]; then
            is_NEVER=`echo $is_MYSQLUP | grep never$`
            if [ -z "$is_NEVER" ]; then
                sed -i "s/$is_MYSQLUP/MYSQLUP=never/g" /etc/cpupdate.conf
            fi
        else
            echo -e "\nMYSQLUP=never" >> /etc/cpupdate.conf
        fi
    else
        echo "" > /etc/cpupdate.conf.governor
        echo "MYSQLUP=never" > /etc/cpupdate.conf
    fi

}

if [ -e /usr/local/cpanel/cpanel ]; then
        if [ -e /usr/local/cpanel/scripts/update_local_rpm_versions ]; then
                if [ ! -e /var/cpanel/rpm.versions.d/cloudlinux.versions ]; then 
                        cp /usr/share/lve/dbgovernor/cpanel/cloudlinux.versions /var/cpanel/rpm.versions.d/cloudlinux.versions
                fi
        else
                if [ ! -e /etc/cpupdate.conf.governor ]; then
                        getMYSQLUP
                fi
                touch /etc/mysqlupdisable
        fi
fi




