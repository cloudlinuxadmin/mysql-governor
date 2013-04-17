#!/usr/bin/python

import glob, os, shutil, stat, string, subprocess

def first_quot(line, isquotf):
	if line[0] == "\"" and isquotf == 0:
		return 1
	return 0

def last_quot(line, isquotf):
	if line[len(line)-1]=='\"' and isquotf == 1:
		return 1
	return 0

def parse_command(command):
	command = command.split(" ")
	isquot=0
	res = ""
	result = []
	for i in range(len(command)):
		if command[i] != "":
			if first_quot(command[i], isquot) == 1:
				isquot = 1
				res = command[i]
				continue
			if last_quot(command[i], isquot) == 1:
				isquot = 0
				res +=" "+command[i]
				result.append(res)
				continue
			result.append(command[i])
	print result
				
		
		

def exec_command(command):
	result = []
	try:
		p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
		while 1:
			output = p.stdout.readline()
			if not output:
				break;
			if output.strip()!="": 
				result.append(output.strip())
	except Exception, inst:
		print "Call process error: "+str(inst) 
	return result
	
def exec_command_out(command):
	os.system(command)

def exec_command_find_substring(command, substring):
	result = exec_command(command)
	for i in result:
		if substring in i:
			return i
	return -1



