#!/bin/bash

#cl7,cl8,cl9
LIBDIR=/usr/lib64
#ubuntu 20.04
grep buntu /etc/os-release > /dev/null 2>&1
if [ $? -eq 0 ]; then
    LIBDIR=/usr/lib
fi

LD_PRELOAD=""
search_ld_preload () {
    for f in $1/*.conf; do
        if [ -f $f ]; then
            var=`cat $f | sed 's/Environment=//' | grep LD_PRELOAD | sed 's/"//g'| sed 's/LD_PRELOAD=//'`
            if [[ -n $var ]]; then
                LD_PRELOAD=$LD_PRELOAD":"$var
            fi
        fi
    done
}

FILE=$LIBDIR/libgovernor_stubs.so
if [ -f "$FILE" ]; then
    search_ld_preload "/etc/systemd/system/mysqld.service.d"
    search_ld_preload "/etc/systemd/system/mariadb.service.d"
    echo "LD_PRELOAD=$LIBDIR/libgovernor.so$LD_PRELOAD" > /usr/share/lve/dbgovernor/governor.env
else
    echo "" > /usr/share/lve/dbgovernor/governor.env
fi

