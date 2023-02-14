#!/opt/alt/python37/bin/python3
# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT

import time
import subprocess
from collections import namedtuple

from governor_package_limitting import fill_gpl_json
from utilities import wait_for_governormysql_service_status

Userlimits = namedtuple("Userlimits", "cpu read write")


def getting_individual_limits_vector(individual_limits):
    """
    Gets a dictionary with real limits of users.
    Returns a vector of 'true/false' values
    instead of real values
    where 'true' is an individual limit
    and 'false' is a package limit.
    Args: limits dictionary with users and their real limits values
    Returns: limits dictionary with users and their true/false meaning
    """
    final_dict = dict()
    def get_vector(limit_values, username):
        limits_dict = dict()
        final_dict.update({username: limits_dict})
        for limits_list, _key in ((limit_values.cpu, 'cpu'),
                                  (limit_values.read, 'read'),
                                  (limit_values.write, 'write')):
            limit_list = list()
            limits_dict.update({_key: limit_list})
            _ = [limit_list.append(int(_value) > 0) for _value in limits_list]

    _ = [get_vector(limit, user) for user, limit in individual_limits.items()]

    return final_dict


def getting_whole_dbctl_list():
    """
    Returns all the individual user limits from the 'dbctl list'
    (except default limits of course)
    Dictionary -> { Username:  namedtuple(cpu, read, write)}
    """
    dbctllimits = dict()
    dbctlorig_listraw = get_dbctlorig_listraw()
    if dbctlorig_listraw:
        for limit_line in dbctlorig_listraw:
            if (limit_line and limit_line.split()[0] != 'default'
                and limit_line.split()[0] != 'user'):
                limit_line = limit_line.split()
                dbctllimits.update(
                    {limit_line[0]: Userlimits(
                        limit_line[1].split('/'),
                        limit_line[2].split('/'),
                        limit_line[3].split('/')
                        )
                    }
                )

    return dbctllimits


def get_dbctlorig_listraw(attempts=3):
    """
    Waiting for results from the utility
    """
    command_ = '/usr/share/lve/dbgovernor/utils/dbctl_orig list-raw --bb'
    while attempts > 0:
        attempts -= 1
        dbctllist = subprocess.run(
            command_, shell=True, text=True, capture_output=True
        )
        if dbctllist.returncode == 0:
            return dbctllist.stdout.split('\n')
        time.sleep(5)
    print('Individual limits vector list will not be added!')
    print(dbctllist.stdout)


def fill_the_individual_limits():
    """
    Writes the individual limits vector to the governor_package_limit.json
    """
    msg = "The db_governor service is inactive, individual limits vector list will not be added!"
    governormysql_status = wait_for_governormysql_service_status()
    if not governormysql_status:
        print(msg)
        return

    _vector = getting_individual_limits_vector(getting_whole_dbctl_list())
    for user, limitsdict in _vector.items():
        fill_gpl_json(
            package=user, cpu=limitsdict['cpu'],
            io_read=limitsdict['read'], io_write=limitsdict['write'],
            serialize=False, set_vector=True
        )


if "__main__" == __name__:
    fill_the_individual_limits()
