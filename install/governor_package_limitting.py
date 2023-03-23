#!/opt/alt/python37/bin/python3
# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#

import pwd
import time
import argparse
from distutils.log import debug
import os
import sys
from os.path import exists
from clcommon.cpapi import cpinfo, admin_packages, resellers_packages
from typing import Dict, List, Tuple
import subprocess
import json
import logging

from utilities import Logger, shadow_tracing, acquire_lock, LockFailedException


DBCTL_BIN = '/usr/share/lve/dbgovernor/utils/dbctl_orig'
PACKAGE_LIMIT_CONFIG = '/etc/container/governor_package_limit.json'
LOCK_FILE = '/var/run/governor_package_limit'
DBCTL_SYNC_LOCK_FILE = '/var/run/governor_package_sync'
DEBUG = False
ENCODING = 'utf-8'


def add_logs():
    """
    Messages related to governor_package_limitting
    """
    logging.basicConfig(
        filename="/usr/share/lve/dbgovernor/governor_package_limitting.log",
        format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)


def debug_log(line, end='\n'):
    """
    Debug output log
    """
    global DEBUG
    if DEBUG:
        print(line, end=end)


def build_parser():
    """
    Build CLI parser
    """
    parser = argparse.ArgumentParser(
        prog="Configure mysqlgovernor limits with Control Panel Packages",
        description="Description: Configure governor-mysql with Control Panel Package limits",
        add_help=False,
        usage='governor_package_limitting.py [COMMAND] [OPTIONS]'
    )
    parser._positionals.title = 'Commands'
    parser._optionals.title = 'Options'

    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Governor package limiting')
    parser.add_argument('--debug', action='store_true', help='Turn on debug mode')

    subparser = parser.add_subparsers(dest='command')

    ################ SET ################
    _set = subparser.add_parser(
        'set',
        help='Set limits for governor packages limits',
        description='Description: Set cpu limit for governor package'
    )
    _set.add_argument('--package', help='Package name', type=str, required=True)
    _set.add_argument('--cpu', help='limit CPU (pct) usage', nargs='+',)
    _set.add_argument('--read', help='limit READ (MB/s) usage', nargs='+')
    _set.add_argument('--write', help='limit WRITE (MB/s) usage', nargs='+')
    _set.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ DELETE ################
    delete = subparser.add_parser(
        'delete',
        help='Delete governor package limits',
        description='Description: Delete governor package limit',
        usage='governor_package_limitting.py delete [PACKAGE_NAME]'
    )
    delete._optionals.title = 'Options'
    delete.add_argument('--package', help='Package name', type=str, required=True)
    delete.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ GET ################
    get = subparser.add_parser(
        'get',
        help='Get governor package limits',
        description='Description: Get governor package limits',
        usage='governor_package_limitting.py get [OPTIONS]',
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=99999)
    )
    get._optionals.title = 'Options'
    g = get.add_mutually_exclusive_group()
    g.add_argument('--package', help='Get package limits', type=str, )
    g.add_argument('--all', help="Get all package limits", action='store_true')

    get.add_argument('--format', help='Show limits in formats: (KB/s), (BB/s), (MB/s). Default is mb',
                     default='mb',choices=['bb', 'kb', 'mb'])

    get._optionals.title = 'Options'
    get.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ GET INDIVIDUAL ################
    get_individual = subparser.add_parser(
        'get_individual',
        help='Get governor package limits vector',
        description='The vector describes which limit is an individual and which is not',
        usage='governor_package_limitting.py get_individual --user=[USER_NAME]'
    )
    get_individual._optionals.title = 'Options'
    get_individual.add_argument('--user', help='Shows a particular user\'s vector', type=str,)
    get_individual.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ SET INDIVIDUAL ################
    _set_individual = subparser.add_parser(
        'set_individual',
        help='Set governor package limits vector',
        description='The vector describes which limit is an individual and which is not',
        usage='governor_package_limitting.py set_individual --user=[USER_NAME] --cpu=[False]*4 --read=[True]*4 --write=[True]*4'
    )
    _set_individual.add_argument('--user', help='Package name', type=str, required=True)
    _set_individual.add_argument('--cpu', help='True/False vector, four values', nargs='+',)
    _set_individual.add_argument('--read', help='True/False vector, four values', nargs='+')
    _set_individual.add_argument('--write', help='True/False vector, four values', nargs='+')
    _set_individual.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ RESET INDIVIDUAL ################
    reset_individual = subparser.add_parser(
        'reset_individual',
        help='Erases information about individual limits',
        description='The user will use a package limits or default limits as result',
        usage='governor_package_limitting.py reset_individual --user=[USER_NAME] --limits=mysql-io,mysql-cpu'
    )
    reset_individual._optionals.title = 'Options'
    reset_individual.add_argument('--user', help='User name', type=str, required=True)
    reset_individual.add_argument('--limits', help='mysql-io or mysql-cpu', type=str)
    reset_individual.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ SYNC ################
    sync = subparser.add_parser(
        'sync',
        help='Synchronize governor package limits',
        description='Description: Apply package limitting configuration to governor',
        usage='governor_package_limitting.py sync'
    )
    sync._optionals.title = 'Options'
    sync.add_argument('--package', help='Package name', type=str, required=False)
    sync.add_argument('--user', help='User name', type=str, required=False)
    sync.add_argument('--debug', action='store_true', help='Turn on debug mode')

    return parser


def cp_packages() -> Dict[str, list]:
    """
    Get packages and it's users.
    Returns:
        (dict): package_name and contained users list
    """
    def update_list_in_a_dict_item(package: str, user: str) -> None:
        """
        Updates a list of users who use the package
        """
        if users_and_packages.get(package):
            users_and_packages[package].append(user)
        else:
            users_and_packages[package] = [user]

    __cpinfo = cpinfo()
    users_and_packages = {}
    # user's packages
    for i in __cpinfo:
        update_list_in_a_dict_item(i[1], i[0])
    # receller's packages
    for usr, pkgs in resellers_packages().items():
        for pkg in pkgs:
            update_list_in_a_dict_item(pkg, usr)

    return users_and_packages


def limits_serializer(args: List, set_vector=False):
    """Convert user input list of string to list of int
    <set_vector=True> -> when use the function to
                         prepare vector instead of values
    For example: ['1,2,3,4'] to -> [1,2,3,4]
    """
    __limits = []

    try:
        if args and isinstance(args, list):
            for i in args[0].split(','):
                if set_vector and 'true' in i.lower():
                    __limits.append(True)
                elif set_vector and 'false' in i.lower():
                    __limits.append(False)
                else:
                    __limits.append(i)
    except Exception as err:
        print(f'Some parameters are incorrect: {err}')
        sys.exit(1)

    if len(__limits) > 4:
        print(f'Some parameters are incorrect. Provided options is more than 4')
        sys.exit(1)

    if __limits and set_vector and len(__limits) != 4:
        print(f'Some parameters are incorrect. Provided options must be equal 4 when you set the vector!')
        sys.exit(1)

    if not __limits and set_vector:
        while len(__limits) < 4:
            __limits.append(False)

    if len(__limits) < 4:
        while len(__limits) < 4:
            __limits.append(0)

    return __limits


def write_config_to_json_file(cfg: dict):
    with acquire_lock(LOCK_FILE, exclusive=True):
        with open(PACKAGE_LIMIT_CONFIG, 'w', encoding=ENCODING) as jsonfile:
            json.dump(cfg, jsonfile)


def read_config_file():
    with acquire_lock(LOCK_FILE, exclusive=True):
        with open(PACKAGE_LIMIT_CONFIG, 'r', encoding=ENCODING) as jsonfile:
            try:
                cfg = json.load(jsonfile)
            except json.JSONDecodeError:
                return {}
    return cfg if cfg else {}


def get_item_from_config_dict(name: str, cfg: dict):
    """Get package from cfg dictionary if exists"""
    cfg = cfg.get(name)
    if cfg:
        cfg = {name: cfg}
    return cfg


def show_default_value_instead_of_zero(name: str, lim_list: list,
                                       default_limits: tuple):
    """
    Replaces 'zero' values by default values
    Args:
        name - cpu or read or write set of limits
        lim_list - lim_list is a current set of limits we'll modify if 'zero'
                   values are present
        default_limits - 'default limits' we'll use instead of 'zero' values
    """
    d_cpu, d_read, d_write = default_limits
    d_limits = {'cpu': d_cpu, 'read': d_read, 'write': d_write}
    # to know which values have not been changed
    indices_of_unchanged_elements = list()
    for _indx, num in enumerate(lim_list):
        if num < 1:
            lim_list[_indx] = d_limits[name][_indx]
        else:
            indices_of_unchanged_elements.append(_indx)

    return indices_of_unchanged_elements


def print_individual_in_json_format(cfg: dict):
    print(json.dumps(cfg, ensure_ascii=False))


def print_config_in_json_format(cfg: dict, size_format, only_section=True):
    default_limits = get_dbctl_limits(format=size_format)
    if only_section:
        cfg = cfg['package_limits']
    for key, val in cfg.items():
        for k, v in val.items():
            # returns the default values instead of 'zero'
            index_list = show_default_value_instead_of_zero(
                k, v, default_limits)
            if k != 'cpu':
                for i in index_list:
                    cfg[key][k][i] = byte_size_convertor(
                        v[i], from_format='bb', to_format=size_format
                    )
    print(json.dumps(cfg, ensure_ascii=False))


def check_if_values_are_not_less_than_zero(cfg):
    for k, v in cfg.items():
        for i in v:
            if i < 0:
                print(f'Value for {k} must be >= 0')
                debug_log(f'Incorrect parameters for {k}')
                debug_log(f'Applied config is {cfg}')
                sys.exit(1)


def fill_gpl_json(package: str, cpu: list = None, io_read: list = None,
                  io_write: list = None, serialize: bool = True,
                  set_vector: bool = False) -> None:
    """
    Setting 'package limits' or 'individual limits' to
    the governor_package_limit.json
    Args:
        package (str): Package name
        cpu (list): cpu limits
        io_read (list): io read limits
        io_write (list): io write limits
        serialize (bool): To serialize or not
        set_vector (bool): True if setting individual limits
    Return:
        None
    """
    cfg = {
        package: {
            'cpu': limits_serializer(cpu, set_vector) if serialize else cpu,
            'read': limits_serializer(io_read, set_vector) if serialize else io_read,
            'write': limits_serializer(io_write, set_vector) if serialize else io_write,
        }
    }

    if not set_vector:
        convert_io_rw_to_bb(cfg[package])
        check_if_values_are_not_less_than_zero(cfg[package])
        section = 'package_limits'
    else:
        section = 'individual_limits'

    config = get_package_limit()
    if config[section].get(package):
        if cpu:
            config[section][package]['cpu'] = cfg[package]['cpu']
        if io_read:
            config[section][package]['read'] = cfg[package]['read']
        if io_write:
            config[section][package]['write'] = cfg[package]['write']
    else:
        config[section][package] = cfg[package]

    debug_log(f'Setting package limit with config: {config}\n')
    write_config_to_json_file(config)
    return


def update_default_limits():
    """
    Update default values in our json from the dbctl list
    """
    config = get_package_limit()
    try:
        config['package_limits'].update({'default': {"cpu": [0] * 4,
                                                     "read": [0] * 4,
                                                     "write": [0] * 4}
                                        }
                                       )
        write_config_to_json_file(config)
    except (KeyError, AttributeError):
        return


def delete_package_limit(package: str):
    """Delete package limits
    Args:
        package (str): Name of package limit to delete
    Returns:
        None
    """
    config = get_package_limit()
    try:
        config['package_limits'].pop(package)
        write_config_to_json_file(config)
        debug_log(f'Deleting package {package} from config')
    except (KeyError, AttributeError) as err:
        print(f'Package name {package} not found')
        debug_log(err)
        return


def reset_individual(username: str, certain_limits: str = None):
    """
    Delete user individual limits vector
    from the governor_package_limit.json, 'individual_limits' section
    """
    help_msg = f"""Vector {username} not found"""

    def reset_all():
        # remove the individual limits from the mysql-governor.xml
        run_dbctl_command([username], 'delete')
        config = get_package_limit()
        try:
            config['individual_limits'].pop(username)
            write_config_to_json_file(config)
            debug_log(f'Deleting vector {username} from config')
        except (KeyError, AttributeError) as err:
            print(help_msg)
            debug_log(err)
            return

    if not certain_limits or certain_limits.lower() == 'all':
        reset_all()
    else:
        _limits = certain_limits.split(',')
        if len(_limits) > 1:
            reset_all()
        else:
            reset_a_certain_limit(username, _limits)


def change_vector_for_a_user(_user: str, limits: list):
    """
    Marks that a particular limits are not individual anymore.
    We can reset individual limits for mysql-cpu or mysql-io.
    Args:
        _user: is a particular user we makes changes for
        limits: vector where non individual limits have to be set
    """
    config = get_package_limit()
    dictionary_to_update = {'mysql-cpu': {'cpu': [False] * 4},
                            'mysql-io': {'read': [False] * 4,
                                         'write': [False] * 4}
                           }
    for lim in limits:
        update_vector = dictionary_to_update.get(lim)
        try:
            config['individual_limits'][_user].update(update_vector)
        except (KeyError, AttributeError) as err:
            return
    write_config_to_json_file(config)


def return_the_individual_limits_to_dbctl(_user: str, limits: list,
                                          saved_limits: tuple):
    """
    Sets the individual limits as they were before because
    the individual limits must not be changed
    Args:
        _user: the user for which individual limits should be set
        limits: mysql-io (read/write) or mysql-cpu set of limits
        saved_limits: individual limits that were set before the
                      general reset of limits for a particular user
    """
    _cpu_limit, _read_limit, _write_limit = saved_limits
    for lim in limits:
        # if we change mysql read/write limits - the individual cpu limits
        # must not be changed!
        if lim == 'mysql-io':
            _cpu_limits = ",".join([str(i) + 'b' for i in _cpu_limit])
            _limit = f'--cpu={_cpu_limits}'
        # the same situation as described above
        elif lim == 'mysql-cpu':
            _read_limit = ",".join([str(i) + 'b' for i in _read_limit])
            _read = f'--read={_read_limit}'
            _write_limit = ",".join([str(i) + 'b' for i in _write_limit])
            _write = f'--write={_write_limit}'
            _limit = f'{_read} {_write}'
        else:
            return

    dbctlset = f'{DBCTL_BIN} set {_user} {_limit}'
    subprocess.run(dbctlset, shell=True, text=True)


def reset_a_certain_limit(username: str, limits: list):
    """
    Makes possible to reset the individual limits for a particular limit.
    For instance we can reset only mysql-cpu or only mysql-io (read/write),
    not both.
    """
    # Saves current individual limits
    saved_limits = get_dbctl_limits(username)
    # Removes all limits (dbctl individual) for a particular user
    run_dbctl_command([username], 'delete')
    # Marks non individual limits (set as <False>)
    # governor_package_limit.json -> individual_limits ->
    # user name -> cpu or read/write
    change_vector_for_a_user(username, limits)
    # Return individual limits for a set of limits which still individual
    return_the_individual_limits_to_dbctl(username, limits, saved_limits)


def get_package_limit(package: str = None, size_format: str = 'mb',
                      print_to_stdout=False, cfg=None):
    """Get package limits
    Args:
        package (str): name of package to get
        print_to_stdout (bool): Print to stdout is used for cli.
        size_format: Print values in specified format. mb, kb, bb
    Returns:
        Package limit configurations or provided package configuration
    """
    cfg = cfg or read_config_file()

    if package:
        cfg = get_item_from_config_dict(package, cfg['package_limits'])
        only_section = False
    else:
        only_section = True

    if print_to_stdout and cfg:
        print_config_in_json_format(cfg, size_format, only_section)

    return cfg


def get_individual(username: str = None, print_to_stdout=False):
    """
    Get individual limits
    Args:
        username: name of user to get
        print_to_stdout (bool): Print to stdout is used for cli.
    Returns:
        Individual limits vector ->
        {"individual_limits": {"user1": {"cpu": [false, false, false, false],
                                         "read": [true, true, true, true],
                                         "write": [true, true, true, true]}}}
    """
    cfg = read_config_file()

    if username:
        cfg = get_item_from_config_dict(username, cfg['individual_limits'])
        if not cfg:
            cfg = {username: {'cpu': [False] * 4,
                              'read': [False] * 4,
                              'write': [False] * 4}
                  }
    else:
        cfg = cfg['individual_limits']

    if print_to_stdout:
        print_individual_in_json_format(cfg)

    return cfg


def run_dbctl_command(users: list, action: str, limits: dict = None):
    """Run dbctl command in os.
    Set or delete limits for all users specified in package
    Args:
        users (list): List of users to apply configuration
        action (str): Set or delete. Set is used both for set and update.
        limits (dict): cpu, read, write in format [int]
    """
    if action == 'set' and not limits:
        print("Limits has not been set")
        sys.exit(1)

    if action == 'delete' and users:
        for user in users:
            command = f'{DBCTL_BIN} delete {user}'
            debug_log(f'Running command: {command}')
            subprocess.run(command, shell=True, text=True)

    if action == 'set' and limits and users:
        for user in users:
            # Returns an empty list when user is absent in dbctl
            # so we need to skip all dbctl actions
            prepare_limits_out = prepare_limits(
                user, package_limit=limits,
                individual_limit=get_individual(user)
            )
            if prepare_limits_out:
                cpu, io_read, io_write = prepare_limits_out
                command = f'{DBCTL_BIN} set {user} --cpu={cpu} --read={io_read} --write={io_write}'
                debug_log(f'Running command: {command}')
                subprocess.run(command, shell=True, text=True)


def dbctl_sync(action: str, package: str = None, user: str = None):
    """Sync package configuration with dbgovernor
    Args:
        action (str): Set or Delete
        package (str): Package name is used with action delete.
                       We can also synchronise for a specific
                       package only with action 'set'
        package (str): User name is used with action 'set'
                       to synchronise for a specific user only
    """
    if not action:
        print("Action not specified")
        sys.exit(1)
    debug_log("Syncing with dbctl")
    __cp_packages = cp_packages()

    if action == 'delete' and package:
        users_to_apply_package = __cp_packages.get(package)
        if users_to_apply_package:
            debug_log(f'Deleting package limits for users: {users_to_apply_package}')
            run_dbctl_command(users_to_apply_package, action)
            return

    if action == 'set':
        _package_limits = get_package_limit(package)
        # Use a specific package (including all users of these package)
        # if package for sync is specified
        # Use all packages otherwise
        package_limits = _package_limits if package else _package_limits['package_limits']

        # To avoid traceback if incorrect package name has been set
        if not package_limits:
            return

        for package_name, limits in package_limits.items():
            users_to_apply_package = __cp_packages.get(package_name)
            if users_to_apply_package:
                if not user:
                    # Sets package limits for all package's users
                    debug_log(f'Setting package limits for users: {users_to_apply_package}')
                    run_dbctl_command(users_to_apply_package, action, limits)
                    continue
                if user in users_to_apply_package:
                    # Sets package limits only for a specific user
                    # if user for sync is specified
                    debug_log(f'Setting package limits for user: {user}')
                    run_dbctl_command([user], action, limits)
                    return


def byte_size_convertor(value: int, from_format: str, to_format: str):
    """Converting integer between formats mb|kb|bb
    Args:
        value (int): Integer value to convert
        from_format (str): To convert from mb|kb|bb
        to_format (str): To convert to mb|kb|bb
    """
    if value < 0:
        return value

    if from_format == 'bb':
        if to_format == 'kb':
            value /= 1024
        elif to_format == 'mb':
            value = value / 1024 / 1024

    elif from_format == 'kb':
        if to_format == 'bb':
            value *= 1024
        elif to_format == 'mb':
            value /= 1024

    elif from_format == 'mb':
        if to_format == 'kb':
            value *= 1024
        elif to_format == 'bb':
            value = value * 1024 * 1024

    return int(value)


def convert_io_rw_to_bb(cfg: dict):
    """Converting MB or KB to bytes
    Parameters from user cli can be bytes, MB or KB.
    Symbol 'b' - bytes, symbol 'k' - kilobytes,
    symbol 'm' or no symbols - megabytes
    [1, 50m, 52428800b, 100k]
    Args:
        cfg (dict): {cpu: [x,x,x,x], read: [x,x,x,x], write: [x,x,x,x,]}
    Returns:
          cfg (dict)
    """
    for k, v in cfg.items():
        if k != 'cpu':
            for i in range(4):
                if isinstance(v[i], str):
                    if 'b' in v[i]:
                        v[i] = int(v[i].replace('b', ''))
                    elif 'k' in v[i]:
                        debug_log(f'Converting kilobytes `{v[i]}` to bytes')
                        v[i] = byte_size_convertor(
                            int(v[i].replace('k', '')),
                            from_format='kb', to_format='bb'
                        )
                    elif 'm' in v[i]:
                        debug_log(f'Converting megabytes `{v[i]}` to bytes')
                        v[i] = byte_size_convertor(
                            int(v[i].replace('m', '')),
                            from_format='mb', to_format='bb'
                        )
                    else:
                        debug_log(f'Converting megabytes `{v[i]}` to bytes')
                        v[i] = byte_size_convertor(
                            int(v[i]),
                            from_format='mb', to_format='bb'
                        )
        else:
            for i in range(4):
                v[i] = int(v[i])

    debug_log('\n')
    return cfg


def trying_to_get_user_in_dbctl_list(user: str, format: str) -> Dict:
    """
    Extract user limits from dbctl list output
    Make additional attempt in case of fail and fallback to default limits
    Args:
        user -> web panel user for which we perform actions
        format -> formats that we use in dbctl (bb, kb, mb)
    Returns:
        specific user limits (cpu, read, write)
    """

    data = _get_dbctl_list_json(format).get(user)
    # make one more attempt in case of new user that wasn't added to dbctl list yet
    if not data:
        default_limits = {
            "cpu": {"current": 0, "short": 0, "mid": 0, "long": 0},
            "read": {"current": 0, "short": 0, "mid": 0, "long": 0},
            "write": {"current": 0, "short": 0, "mid": 0, "long": 0}
        }
        # restart db_governor service to add the user to the dbctl list immediately
        os.system('/usr/share/lve/dbgovernor/mysqlgovernor.py --dbupdate')
        time.sleep(1)
        os.system('service db_governor restart &> /dev/null')
        time.sleep(1)
        # if user limits still unavailable - just return a structure with zero values
        data = _get_dbctl_list_json(format).get(user) or default_limits
    return data


def _get_dbctl_list_json(format: str) -> Dict:
    dbctl_limits = f'{DBCTL_BIN} list-json --{format}'
    output = subprocess.run(dbctl_limits, shell=True,
                            text=True, capture_output=True)
    _data = output.stdout
    try:
        data = json.loads(_data)
    except json.JSONDecodeError:
        logging.debug(f"<{DBCTL_BIN} list-json --{format}> returns non json data!")
        logging.debug(f"stdout -> {output.stdout}")
        logging.debug(f"stderr -> {output.stderr}")
        sys.exit(1)
    return data


def get_dbctl_limits(user: str = 'default', format: str = 'bb') -> Tuple:
    """
    Gets dbctl limits list and returns a tuple of individual limits
    (cpu, read, write) for a specific user.
    Running this function without 'user' argument returns
    the default limits.
    Args: user   -> to get an individual user limits, returns 'default'
                    if hasn't been set
          format -> all available formats we use in dbctl:
                    bb - bytes
                    kb - kilobytes
                    mb - megabytes
    Returns: a tuple of lists ([cpu],[read],[write]),
             or blank tuple if user has not been found
    """
    individual_limits = trying_to_get_user_in_dbctl_list(user, format)

    individual_cpu_limit = (
        individual_limits['cpu']['current'],
        individual_limits['cpu']['short'],
        individual_limits['cpu']['mid'],
        individual_limits['cpu']['long']
    )

    individual_read_limit = (
        individual_limits['read']['current'],
        individual_limits['read']['short'],
        individual_limits['read']['mid'],
        individual_limits['read']['long']
    )

    individual_write_limit = (
        individual_limits['write']['current'],
        individual_limits['write']['short'],
        individual_limits['write']['mid'],
        individual_limits['write']['long']
    )

    debug_log(f'{user}\'s individual limits are: ', end='')
    debug_log(f'cpu: {individual_cpu_limit}, read: {individual_read_limit}, write: {individual_write_limit}')

    return individual_cpu_limit, individual_read_limit, individual_write_limit


def get_the_limits_set(limits_set: list) -> Tuple:
    """
    Here we have twelve values:
    -> four per cpu
    -> four per read
    -> four per write
    Here we divide them to conviniate representation
    """
    cpu = tuple(limits_set[0:4])
    read = tuple(limits_set[4:8])
    write = tuple(limits_set[8:])

    return cpu, read, write


def set_default_limit(package_limit: dict) -> Tuple:
    """
    Defines the limits (cpu, read, write). Uses package limits or
    default limits depending on values. If package value is greater
    than zero - use it, otherwise use  default value.
    """
    package_cpu_limit = package_limit.get('cpu')
    package_read_limit = package_limit.get('read')
    package_write_limit = package_limit.get('write')

    all_limits = list()
    for tuple_of_limits_lists in (package_cpu_limit,
                                  package_read_limit,
                                  package_write_limit):
        for n in tuple_of_limits_lists:
            # values of package limit and default limit (0) respectively
            all_limits.append(n) if n > 0 else all_limits.append(0)

    return get_the_limits_set(all_limits)


def ensures_the_individual_limits_still_set(
    vector: dict, default_or_package_limit: tuple,
    individual_limits: tuple) -> Tuple:
    """
    Sets the individual limit instead of <package limit/default limit>
    if vector value is <True> for the certain limit.
    """
    all_limits = list()
    individual_cpu_limit, individual_read_limit, individual_write_limit = individual_limits
    dorp_cpu_limit, dorp_read_limit, dorp_write_limit = default_or_package_limit
    vectors = vector.values()

    for vector_dict in vectors:
        cpu_vectors = vector_dict['cpu']
        read_vectors = vector_dict['read']
        write_vectors = vector_dict['write']

    # <data_set> contains a 'vector list', an 'individual limits' list
    # and a current list of limits collected from the package limits
    # or default limits
    for data_set in (
        (cpu_vectors, individual_cpu_limit, dorp_cpu_limit),
        (read_vectors, individual_read_limit, dorp_read_limit),
        (write_vectors, individual_write_limit, dorp_write_limit)
    ):
        for n in zip(data_set[0], data_set[1], data_set[2]):
            # If vector is True
            if n[0]:
                all_limits.append(n[1])
            # If vector is False
            else:
                all_limits.append(n[2])

    return get_the_limits_set(all_limits)


def prepare_limits(user: str, package_limit: Dict, individual_limit: Dict) -> List:
    """Prepare Limits with algorithm
    First of all sets the package limits or default limits,
    than sets the individual limits (dependin on vector values)
    For example:
    Pack1 Package limit for cpu is: [100, 0, 65, 40]
    Default Package limit is:       [50, 90, 0, 50]
    Individual limit is:            [150, not_set, not_set, not_set]
    Result will be:                 [150, 90, 65, 40]
    """
    cpu_limit, read_limit, write_limit = ensures_the_individual_limits_still_set(
        individual_limit,
        set_default_limit(package_limit),
        get_dbctl_limits(user)
    )

    try:
        # with 'b' symbol to set bytes using 'dbctl' tool
        cpu = ','.join(str(x) for x in cpu_limit)
        io_read = ','.join(str(x) + 'b' for x in read_limit)
        io_write = ','.join(str(x) + 'b' for x in write_limit)
        debug_log(f'Limits after calculation for {user} is:')
        debug_log(f'cpu: [{cpu}], read: [{io_read}], write: [{io_write}]')
        return cpu, io_read, io_write
    except TypeError as err:
        print(f'Some limits are not given: {err}')
        sys.exit(1)


def get_all_packages():
    """
    Gets all packages: admin packages and resellers packages either.
    """
    all_packages = admin_packages()
    for i in resellers_packages().values():
        for n in i:
            if n not in all_packages:
                all_packages.append(n)

    return all_packages


def sync_with_panel():
    # won't do MYSQLG-789
    """
    Just getting package names and applying default values [0,0,0,0]
    """
    cfg = read_config_file()
    for package in get_all_packages():
        if not get_package_limit(package, cfg=cfg):
            fill_gpl_json(
                package=package
            )
            cfg = read_config_file()


def turn_on_debug_if_user_enabled_debug_mode(opts):
    if opts.debug:
        global DEBUG
        DEBUG = True


def ensure_json_presence():
    """
    The governor_package_limit.json file must always be present!
    Even if someone delete the json config and its content.
    """
    content = {"package_limits": {}, "individual_limits": {}}

    if not exists(PACKAGE_LIMIT_CONFIG):
        write_config_to_json_file(content)
        return

    json_ = read_config_file()
    for element in content.keys():
        if not json_.get(element):
            json_.update({element: {}})
            write_config_to_json_file(json_)


def main(argv):
    """
    Run main actions
    """
    shadow_tracing(False)

    parser = build_parser()
    if not argv:
        parser.print_help()
        sys.exit(1)

    opts = parser.parse_args(argv)

    turn_on_debug_if_user_enabled_debug_mode(opts)
    ensure_json_presence()
    add_logs()

    if opts.command == 'set':
        fill_gpl_json(opts.package, opts.cpu, opts.read, opts.write)
        dbctl_sync('set')
    elif opts.command == 'get':
        sync_with_panel()
        update_default_limits()
        get_package_limit(opts.package, opts.format, print_to_stdout=True)
    elif opts.command == 'delete':
        delete_package_limit(opts.package)
        dbctl_sync('delete', opts.package)
    elif opts.command == 'sync':
        # to avoid excessive calls of sync command just ignore too frequent calls
        try:
            with acquire_lock(DBCTL_SYNC_LOCK_FILE, exclusive=True, attempts=1):
                dbctl_sync('set', opts.package, opts.user)
        except LockFailedException as err:
            debug_log(f'Excessive sync call ignored')
            pass
    elif opts.command == 'get_individual':
        get_individual(opts.user, print_to_stdout=True)
    elif opts.command == 'set_individual':
        fill_gpl_json(opts.user, opts.cpu, opts.read, opts.write,
                      serialize=True, set_vector=True)
    elif opts.command == 'reset_individual':
        reset_individual(opts.user, opts.limits)
        dbctl_sync('set')
    else:
        parser.print_help()
        sys.exit(1)


if "__main__" == __name__:
    main(sys.argv[1:])
