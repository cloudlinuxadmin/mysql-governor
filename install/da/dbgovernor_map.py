#!/usr/bin/python

import os
import pwd
import glob
import string
import MySQLdb

def get_dauser( path ):
    users = {}
    os.chdir( path )
    dirList = glob.glob( './*' )

    for userDir in dirList:
        if os.path.isdir( userDir ):
            fileDomains = path + '/' + userDir + '/domains.list'
            try:
                f = open( fileDomains )
                if len( f.readline() ) > 0:
                    userName = userDir[ 2: ]
                    p = pwd.getpwnam( userName )
                    users[userName] = p.pw_uid
                f.close()
            except IOError:
                print( "No file " + fileDomains )

    return users

def get_account_list():
    conf_name = '/usr/local/directadmin/conf/mysql.conf'
    accountList = {}
    params = {}
    userList = get_dauser( '/usr/local/directadmin/data/users' )

    try:
        f = open( conf_name )
        for line in f.readlines():
            p = line.split( '=' )
            params[ p[ 0 ].strip() ] = p[ 1 ].strip()
        f.close()
    except IOError:
        print( "No file " + conf_name )
        
    try:
        import MySQLdb
    except:
        print_error_message( 'Error: package "MySQL-python" is not installed.' )
        return accountList
        
    if 'host' in params:
        host_ = params[ 'host' ]
    else:
        host_ = 'localhost'
    user_ = params[ 'user' ]
    passwd_ = params[ 'passwd' ]

    for ul in userList:
        user = [ul, userList[ul]]
        accountList[ ul  ] =  user

    try:
        con = MySQLdb.connect( host = host_, user = user_, passwd = passwd_, db = "mysql" )
        cur = con.cursor()
        cur.execute( 'set names `utf8`' )
        cur.execute( 'select `user` from db group by `user` order by `user`' )
        result = cur.fetchall()
        for row in result:
            try:
                username = row[0].split('_')[0].strip()
                user = [username, userList[username]]
                accountList[ row[1].strip().replace('\\', '')  ] =  user
            except KeyError:
                #db_user has no real user
                pass
        con.close()
    except MySQLdb.Error:
        print( con.error() )
    
    return accountList

def listUserMap( fileName ):
    listUserMap = {}
    try:
        f = open( fileName )
        for line in f:
                ( user_, account_, id_ ) = line.split()
                listUserMap[user_] = [ account_, id_ ]
        f.close()
    except IOError:
        pass

    return listUserMap

def writeFileMap( fileName ):
    mapList = listUserMap( fileName )
    accountList = get_account_list()

    f = open( fileName, 'w' )
    for db_user in accountList.keys():
        mapList[db_user] = accountList[db_user]

    for db_user, account in mapList.iteritems():
        line = "%s %s %s\n" % (db_user, account[0], account[1])
        f.writelines( line )
    f.close()

if __name__ == '__main__':
    writeFileMap( '/etc/container/dbuser-map' )
