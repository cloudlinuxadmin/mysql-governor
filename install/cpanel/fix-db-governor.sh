#!/bin/bash

. /usr/share/lve/dbgovernor/utils/db_install_common.sh

echo "ReInstallation mysql-devel"
if [ "$3" == "--stable" ]; then
  installDbDevel "$1"
else
  installDbTestDevel "$1"
fi

