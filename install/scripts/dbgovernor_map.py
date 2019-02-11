#!/opt/alt/python27/bin/python

# -*- coding: utf-8 -*-

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
import glob
import os
import pwd
import sys


def get_dauser(path):
    """
    Get list of users
    :param path:
    :return:
    """
    users = {}
    os.chdir(path)
    dirList = glob.glob('./*')

    for userDir in dirList:
        if os.path.isdir(userDir):
            fileDomains = path + '/' + userDir + '/domains.list'
            try:
                f = open(fileDomains)
                if len(f.readline()) > 0:
                    userName = userDir[2:]
                    try:
                        p = pwd.getpwnam(userName)
                        users[userName] = p.pw_uid
                    except KeyError:
                        print "Warning: user '%s' has no uid!" % userName
                f.close()
            except IOError:
                print "No file " + fileDomains

    return users


def get_account_list():
    """
    Get list of accounts
    :return:
    """
    conf_name = '/usr/local/directadmin/conf/mysql.conf'
    accountList = []
    params = {}
    userList = get_dauser('/usr/local/directadmin/data/users')

    try:
        f = open(conf_name)
        for line in f.readlines():
            p = line.split('=', 1)
            if len(p) > 1:
                params[p[0].strip()] = p[1].strip()
        f.close()
    except IOError:
        print "No file " + conf_name

    try:
        import MySQLdb
    except ImportError:
        print >> sys.stderr, 'Error: package "MySQL-python" is not installed.'
        return accountList

    if 'host' in params:
        host_ = params['host']
    else:
        host_ = 'localhost'
    user_ = params['user']
    passwd_ = params['passwd']

    for ul in userList:
        accountList.append((ul, ul, userList[ul]))

    try:
        if 'socket' in params:
            con = MySQLdb.connect(unix_socket=params['socket'], user=user_,
                                  passwd=passwd_, db="mysql")
        else:
            con = MySQLdb.connect(host=host_, user=user_, passwd=passwd_,
                                  db="mysql")
        cur = con.cursor()
        cur.execute('set names `utf8`')
        cur.execute('select `user` from db group by `user` order by `user`')
        result = cur.fetchall()
        for row in result:
            try:
                username = row[0].split('_')[0].strip()
                accountList.append((row[0], username, userList[username]))
            except KeyError:
                # db_user has no real user
                pass
        con.close()
    except MySQLdb.Error:
        print con.error()

    return accountList


def writeFileMap(fileName):
    """
    Write file with user-account accordance
    :param fileName:
    :return:
    """
    accountList = get_account_list()

    f = open(fileName + '.tmp', 'w')
    for db_user, account_name, account_id in set(accountList):
        line = "%s %s %s\n" % (db_user, account_name, account_id)
        f.writelines(line)
    f.close()
    os.rename(fileName + '.tmp', fileName)


if __name__ == '__main__':
    writeFileMap('/etc/container/dbuser-map')
