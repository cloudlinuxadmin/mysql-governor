#!/bin/bash

# Wait for the dpkg/apt lock (may be locked by the update process)
while fuser /var/lib/dpkg/lock >/dev/null 2>&1 \
   || fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 \
   || fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
    sleep 1
done

# Check if any cl-mysql80* or cl-mariadb103* package is installed with epoch
epoch_mysql_packages=$(dpkg -l 'cl-mysql80*' | awk '/^ii/ && $2 ~ /^cl-mysql80/ && $3 ~ /^1:/ {print $2, $3}')
epoch_mariadb_packages=$(dpkg -l 'cl-mariadb103*' | awk '/^ii/ && $2 ~ /^cl-mariadb103/ && $3 ~ /^2:/ {print $2, $3}')

# If any mysql80 package found with epoch 1, install the two required packages for transition
if [ -n "$epoch_mysql_packages" ]; then
  apt-get install cl-mysql80-epoch-removal -y
  apt-get install cl-mysql80-transitional -y
fi

# If any cl-mariadb103 package found with epoch 2, install the two required packages for transition
if [ -n "$epoch_mariadb_packages" ]; then
  apt-get install cl-mariadb103-epoch-removal -y
  apt-get install cl-mariadb103-transitional -y
fi

# Remove transition cron job if exists
if [ -e "/etc/cron.d/cl_transition_job" ]; then
  rm -f /etc/cron.d/cl_transition_job
fi