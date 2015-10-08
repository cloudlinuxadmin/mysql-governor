#!/bin/bash
#1 - path to log file with out info
#2 - path to binary file

while IFS='' read -r line || [[ -n "$line" ]]; do
echo "$line" | cut -d'#' -f1
IFS='#' read -a array <<< "$line"
for element in "${array[@]:1}"
do
addr=$(echo "$element" | cut -d'[' -f2 | cut -d']' -f1)
/usr/bin/eu-addr2line -e "$2" -f -i "$addr"
done
done < "$1"