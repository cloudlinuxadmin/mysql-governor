#!/usr/bin/python

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT

import sys
import subprocess

fileauthors = dict()
emptystring = ""

cmd = subprocess.Popen("egrep -R -i \" author\" *", shell=True, stdout=subprocess.PIPE)
for line in cmd.stdout:
    index = line.lower().find("author")
    author = line[index+7:].strip(' \n\t')
    index = line.find(":")
    filename = line[0:index].strip(' \n\t')
    if fileauthors.get(filename, emptystring) != emptystring:
        fileauthors[filename] = fileauthors[filename] + ", " + author
    else:
        fileauthors[filename] = author

for fname in fileauthors:
    print("{} {}".format(fname, fileauthors[fname]))
