#!/usr/local/cpanel/3rdparty/bin/python
import sys
import pwd
map_file = '/etc/container/dbuser-map'


def writeFileMap(action, acc_user, new_user, old_user=None):
    """

    :param db_user:
    :param acc_user:
    :param action:
    :return:
    """
    acc_user_id = pwd.getpwnam(acc_user).pw_uid
    new_map_line = '{db_u} {acc_u} {uid}'.format(db_u=new_user,
                                                 acc_u=acc_user,
                                                 uid=acc_user_id)
    if action == 'create_user':
        pass
        # print 'add user to map file'
        # print 'user %s from acc %s' % (new_user, acc_user)
        # with open(map_file, 'rb') as dbgovernor_map:
        #     lines = dbgovernor_map.readlines()
        #     lines.append(new_map_line)

    elif action == 'rename_user':
        pass
        # old_map_line = '{db_u} {acc_u} {uid}'.format(db_u=old_user,
        #                                              acc_u=acc_user,
        #                                              uid=acc_user_id)
        # print 'update user in map file'
        # print 'old_user %s' % old_user
        # print 'new_user %s' % new_user
        # with open(map_file, 'ab') as dbgovernor_map:
        #     lines = [l for l in dbgovernor_map.readlines() if l != old_map_line]
        #     lines.append(new_map_line)
        #     dbgovernor_map.writelines(lines)
    elif action == 'delete_user':
        pass
        # print 'remove user from map file'
        # print 'user %s from acc %s' % (new_user, acc_user)
        # with open(map_file, 'ab') as dbgovernor_map:
        #     lines = [l for l in dbgovernor_map.readlines() if l != new_map_line]
        #     dbgovernor_map.writelines(lines)


if __name__ == '__main__':
    # print sys.argv
    action = sys.argv[1].split('::')[-1]
    account_user = sys.argv[2]
    if action == 'rename_user':
        new_mysql_user = sys.argv[3]
        old_mysql_user = sys.argv[4]
        writeFileMap(action, account_user, new_mysql_user, old_mysql_user)
    else:
        mysql_user = sys.argv[3]
        writeFileMap(action, account_user, mysql_user)
