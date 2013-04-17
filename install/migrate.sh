#!/bin/bash

# Old base directory for SecureLVE. Do NOT change to "cagefs"!
BASEDIR=/var/securelve

currentpath=$(pwd)
mode_set=0

if [ -d $BASEDIR ]
then

# CageFS is enabled ?
if [ ! -e /etc/cagefs/users.enabled.save -a ! -e /etc/cagefs/users.disabled.save ]; then

if [ ! -e /etc/cagefs/users.enabled ]; then
  if [ ! -e /etc/cagefs/users.disabled ]; then
    # /usr/sbin/cagefsctl --disable-all
    mkdir -p /etc/cagefs/users.enabled
    if [ ! -e /etc/cagefs/users.enabled ];then
      echo "Error: failed to set CageFS mode"
    else
      mode_set=1
    fi
  fi
fi

fi

cd $BASEDIR
for dirname in *; do
    if [ -r "$dirname/etc/passwd" ];then
        # echo "Processing $dirname ..."

        # Obtain current shell for user (in real system)
        cur_shell=$(cat /etc/passwd | grep -m 1 -e "$dirname" | grep -o -P -e '[^:]+$')
        if [ $? != 0 ];then
            # echo "User $dirname does not exist in real system. skipping..."
            continue
        fi

        if ! echo "$cur_shell" | grep "securelve_sh"
        then
            # echo "User $dirname is disabled in SecureLVE. skipping..."
            continue
        fi

        # Obtain new shell for user
        shell=$(cat $dirname/etc/passwd | grep -m 1 -e "$dirname" | grep -o -P -e '[^:]+$')
        if [ $? != 0 ];then
            echo "Error while processing $dirname"
            # cd $currentpath
            # exit 1
            continue
        fi

        echo "Set shell $shell for user $dirname"
        chsh -s $shell $dirname
        if [ $? != 0 ];then
            echo "Error while changing shell for user $dirname"
            # cd $currentpath
            # exit 1
            continue
        fi

        if [ $mode_set -eq 1 ]; then
            echo "Enable CageFS for user $dirname"
            prefix=$(/usr/sbin/cagefsctl --getprefix $dirname)
            if [ $? != 0 ];then
                echo "Error while enabling CageFS for user $dirname"
                continue
            fi
            mkdir -p /etc/cagefs/users.enabled/$prefix
            touch /etc/cagefs/users.enabled/$prefix/$dirname
            if [ $? != 0 ];then
                echo "Error while enabling CageFS for user $dirname"
                continue
            fi
        fi
    fi
done

fi

sed -i -e '/\/usr\/sbin\/jk_chrootsh/d' /etc/shells
if [ $? != 0 ];then
    echo "Error while deleting shell from /etc/shells"
    cd $currentpath
    exit 1
fi

sed -i -e '/\/usr\/sbin\/securelve_sh/d' /etc/shells
if [ $? != 0 ];then
    echo "Error while deleting shell from /etc/shells"
    cd $currentpath
    exit 1
fi

cd $currentpath
