#!/usr/bin/python

import os
import pwd
import glob
import string
import MySQLdb

def isset( variable ):
	return variable in locals() or variable in globals()
    
def get_dauser( path ):
    users = []
    os.chdir( path )
    dirList = glob.glob( './*' )

    for userDir in dirList:
        if os.path.isdir( userDir ):
            fileDomains = path + '/' + userDir + '/domains.list'
            try:
                f = open( fileDomains )
                if len( f.readline() ) > 0:
                    userName = userDir[ 2: ]
                    user_id_ = []
                    user_id_.append( userName )
                    p = pwd.getpwnam( userName )
                    user_id_.append( p.pw_uid )
                    users.append( user_id_ )
                f.close()
            except IOError:
                print( "No file " + fileDomains )

    return users

def get_dauser_full( path ):
    users = []
    os.chdir( path )
    dirList = glob.glob( './*' )

    for userDir in dirList:
        if os.path.isdir( userDir ):
            userName = userDir[ 2: ]
            user_id_ = []
            user_id_.append( userName )
            p = pwd.getpwnam( userName )
            user_id_.append( p.pw_uid )
            users.append( user_id_ )

    return users

def get_account_list():
    conf_name = '/usr/local/directadmin/conf/mysql.conf'
    accountList = {}
    params = {}
    
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
    try:
        con = MySQLdb.connect( host = host_, user = user_, passwd = passwd_, db = "mysql" )
        cur = con.cursor()
        cur.execute( 'set names `utf8`' )
        cur.execute( 'select `user`,`db` from db order by `user`' )
        result = cur.fetchall()
        for row in result:
            accountList[ row[ 0 ].strip() ] =  row[ 1 ].strip()
        con.close()
    except MySQLdb.Error:
        print( con.error() )
    
    return accountList

def checkUserMap( fileName ):
    listUserMap = []
    try:
        f = open( fileName )
        listUserMap = f.readlines()
        f.close()
    except IOError:
        pass

    indexDel = []
    listUserDA = get_dauser( '/usr/local/directadmin/data/users' )
    for userMap in listUserMap:
        ( user_, account_, id_ ) = userMap.split()
        ind = 0
        for userDA in listUserDA:
            if user_ == userDA[ 0 ] and id_ == str( userDA[ 1 ] ):
                indexDel.append( ind )
            ind = ind + 1

    ind = 0
    userList = []
    for userDA in listUserDA:
        iDel = 0
        for i in indexDel:
            if i == ind:
                iDel = 1

        if iDel == 0:
            userList.append( userDA )
        ind = ind + 1

    return userList

def writeFileMap( fileName ):
    userList = checkUserMap( fileName )
    accountList = get_account_list()

    f = open( fileName, 'a' )
    for userList_ in userList:
        for key in accountList.keys():
            if userList_[ 0 ] == key:
                account_name = key + "_" + accountList[ key ]
                break
            else:
                account_name = None
        if account_name != None:
            line = userList_[ 0 ] + ' ' + account_name + ' ' + str( userList_[ 1 ] ) + '\n'
        else:  
            line = userList_[ 0 ] + ' ' + userList_[ 0 ] + ' ' + str( userList_[ 1 ] ) + '\n'
        f.writelines( line )
    f.close()

if __name__ == '__main__':
    writeFileMap( '/etc/container/dbuser-map' )
