#!/opt/alt/python37/bin/python3
# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#

import subprocess
from collections import namedtuple

from governor_package_limitting import (
    getting_individual_limits_vector, fill_gpl_json)

Userlimits = namedtuple("Userlimits", "cpu read write")


def getting_whole_dbctl_list():
    """
    Returns all the individual user limits from the 'dbctl list'
    (except default limits of course)
    Dictionary -> { Username:  namedtuple(cpu, read, write)}
    """
    dbctllist = subprocess.run(
        '/usr/share/lve/dbgovernor/utils/dbctl_orig list-raw --bb | /usr/bin/tail -n +2',
        shell=True, text=True, capture_output=True
    )

    dbctllimits = dict()
    for limit_line in dbctllist.stdout.split('\n'):
        if limit_line and limit_line.split()[0] != 'default':
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


def fill_the_individual_limits():
    """
    Writes the individual limits vector to the governor_package_limit.json
    """
    _vector = getting_individual_limits_vector(getting_whole_dbctl_list())
    for user, limitsdict in _vector.items():
        fill_gpl_json(
            package=user, cpu=limitsdict['cpu'],
            io_read=limitsdict['read'], io_write=limitsdict['write'],
            serialize=False, set_vector=True
        )


if "__main__" == __name__:
    fill_the_individual_limits()
