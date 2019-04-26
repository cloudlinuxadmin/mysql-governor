#!/bin/bash


#runs analyzers for c code:

#cppcheck
cppcheck -v --enable=all --xml -D__x86_64__ -DLINUX=2 -I/usr/include -I/usr/include/linux -Isrc src 2>report_cppcheck.xml

#rats
rats -w 3 --xml src &>report_rats.xml

#vera++
path_to_project=$(pwd)
pushd /opt/vera
find ${path_to_project}/src/ -name "*.c" -o -name "*.h"|vera++ -s -d \
-c ${path_to_project}/report_vera.xml
popd

#compiler-gcc
sh build.sh &>compiler-gcc-log.log
cat compiler-gcc-log.log|grep warning &>compiler-gcc-fin.log
