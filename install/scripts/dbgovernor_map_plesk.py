#!/opt/alt/python27/bin/python
import pwd
import os
import MySQLdb
from clcommon import cpapi

psa_conf = '/etc/psa/psa.conf'
db = 'psa'


def read_mysql_conn_params():
    """
    Retrieve mysql connection parameters:
    username, password, socket (if exists)
    :return: dict {login: , pass: , socket:}
    """
    access = cpapi.db_access()
    with open(psa_conf, 'rb') as conf:
        mysql_sock = [l.strip() for l in conf.readlines() if 'MYSQL_SOCKET' in l]
    if mysql_sock:
        access['socket'] = mysql_sock[0].split(' ')[1]
    return access


def get_users_data():
    """
    Retrieve Plesk users data from mysql:
        psa_db_users - intersection of mysql.user and psa.db_users tables
        psa_mapped_users - mapping of psa.db_users and psa.sys_users,
                            intersected with mysql.user too
    :return: psa_db_users - list [db_usernames]
             psa_mapped_users - dict {db_username: sys_username}
    """
    conn_params = read_mysql_conn_params()
    dbhost = conn_params.get('host', 'localhost')

    try:
        if 'socket' in conn_params:
            con = MySQLdb.connect(unix_socket=conn_params['socket'],
                                  user=conn_params['login'],
                                  passwd=conn_params['pass'], db=db)
        else:
            con = MySQLdb.connect(host=dbhost, user=conn_params['login'],
                                  passwd=conn_params['pass'], db=db)
        cur = con.cursor()
        cur.execute('select db.login from mysql.user as mysql, db_users as db where mysql.user = db.login')
        psa_db_users = [u[0] for u in cur.fetchall()]
        cur.execute('select db.login, sys.login from mysql.user as mysql, sys_users as sys, db_users as db where mysql.user = db.login and db.dom_id = sys.id;')
        psa_mapped_users = {u[0]: u[1] for u in cur.fetchall()}
        con.close()
    except MySQLdb.Error:
        print con.error()
        return [], {}

    return psa_db_users, psa_mapped_users


def get_mapped_users_list():
    """
    Map db users to system users.
    If no system user mapped to db user, it is set to "restricted" with uid 3
    If no uid found for system user, it is set to 3
    :return: list of tuples [(db_user, sys_user, sys_user_uid)]
    """
    acct_data = list()
    psa_db_users, psa_mapped_users = get_users_data()

    # inspect all Plesk db users
    for db_user in set(psa_db_users):
        if db_user not in psa_mapped_users:
            # failed to map db user to system one
            acct_data.append((db_user, 'restricted', 3))
        else:
            # found mapping
            sys_user = psa_mapped_users[db_user]
            try:
                uid = pwd.getpwnam(sys_user).pw_uid
            except Exception:
                # failed to get uid for system user
                uid = 3
            acct_data.append((db_user, sys_user, uid))

    return acct_data


def write_dbuser_map(filename='/etc/container/dbuser-map'):
    """
    Write file with user-account accordance
    :param filename: result file name
    """
    accounts = get_mapped_users_list()

    lines = ["%s %s %s\n" % (db_user, account_name, account_id)
             for db_user, account_name, account_id in set(accounts)]

    with open(filename + '.tmp', 'w') as map_file:
        map_file.writelines(lines)

    os.rename(filename + '.tmp', filename)


if __name__ == '__main__':
    write_dbuser_map()
