#!/usr/bin/python

import sys
import subprocess

fileauthors = dict()
emptystring = ""
simplefprefix = "./"
authortpl = "AUTHOR--"

with open(sys.argv[1], "r") as fauthor_csv:
    for line in fauthor_csv:
        index = line.find(" ")
        filename = line[0:index]
        author = line[index:].strip(' \n\t')
        fileauthors[filename] = author

cmd = subprocess.Popen("find . -type f", shell=True, stdout=subprocess.PIPE)
for line in cmd.stdout:
    filename = line.strip(' \n\t')
    if line[0:2] == simplefprefix:
        filename = filename[2:]
        author = fileauthors.get(filename, emptystring)
        if author != emptystring:
            cmd = "sed -i s/' {}'/' Author: {}'/g {}".format(authortpl, author, filename)
            subprocess.Popen(cmd, shell=True)
        else:
            cmd = "sed -i '/ {}/d' {}".format(authortpl, filename)
            subprocess.Popen(cmd, shell=True)
