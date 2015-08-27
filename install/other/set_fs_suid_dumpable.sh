#/bin/bash

echo "Set FS suid_dumpable for governor to work correctly"
sysctl -w fs.suid_dumpable=1
if [ -e /etc/sysctl.conf ]; then
    SDMP=`cat /etc/sysctl.conf | grep "fs.suid_dumpable=1"`
    if [ -z "$SDMP" ]; then
	echo "Add to /etc/sysctl.conf suid_dumpable instruction for governor to work correctly"
	cp -f /etc/sysctl.conf /etc/sysctl.conf.bak 
	echo "fs.suid_dumpable=1" >> /etc/sysctl.conf
    else
	echo "Everything is present in /etc/sysctl.conf for governor to work correctly"
    fi
else
    echo "Create /etc/sysctl.conf for governor to work correctly"
    echo "fs.suid_dumpable=1" >> /etc/sysctl.conf
fi