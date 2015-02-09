#!/bin/bash

echo "Check for mysql pids and upgrade marker"

if [ -e /var/lib/mysql/RPM_UPGRADE_MARKER ]; then
    mv -f /var/lib/mysql/RPM_UPGRADE_MARKER /var/lib/mysql/RPM_UPGRADE_MARKER.old
fi

#if [ -e /var/lib/mysql ]; then
#    rename .pid .pid.old /var/lib/mysql/*.pid 2>/dev/null
#fi