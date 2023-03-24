#!/bin/bash

#cl7,cl8,cl9
LIBDIR=/usr/lib64
#ubuntu 20.04
grep buntu /etc/os-release > /dev/null 2>&1
if [ $? -eq 0 ]; then
    LIBDIR=/usr/lib
fi
FILE=$LIBDIR/libgovernor_stubs.so
if [ -f "$FILE" ]; then
    echo "LD_PRELOAD=$LIBDIR/libgovernor.so" > /usr/share/lve/dbgovernor/governor.env
else
    echo "" > /usr/share/lve/dbgovernor/governor.env
fi

