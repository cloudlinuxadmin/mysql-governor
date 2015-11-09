#!/bin/bash

. /usr/share/lve/dbgovernor/utils/db_install_common.sh

if [ -f "$mysqlTypeFileSet" ]; then
  SQL_VERSION_=`cat $mysqlTypeFileSet`
else
  SQL_VERSION_="auto"
fi

echo -n "$SQL_VERSION_"
