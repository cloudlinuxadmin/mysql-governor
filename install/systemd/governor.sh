#!/bin/bash

LIBDIR=/usr/lib64
FILE=$LIBDIR/libgovernor_stubs.so
if [ -f "$FILE" ]; then
    echo "LD_PRELOAD=$LIBDIR/libgovernor.so" > /usr/share/lve/dbgovernor/governor.env
else
    echo "" > /usr/share/lve/dbgovernor/governor.env
fi

