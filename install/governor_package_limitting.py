#!/opt/alt/python37/bin/python3
# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#

import argparse
import os
import sys
from utilities import Logger, shadow_tracing
from clcommon.cpapi import cpinfo, admin_packages
from typing import Dict, List
import yaml
import subprocess
import json
from math import ceil

LOG_FILE_NAME = "/usr/share/lve/dbgovernor/governor_package_limitting.log"
PACKAGE_LIMIT_CONFIG = '/etc/container/governor_package_limit.yaml'
DEBUG = False

DEFAULT_PACKAGE_LIMITS = {
    'cpu': [-1, -1, -1, -1],
    'read': [-1, -1, -1, -1],
    'write': [-1, -1, -1, -1],
}


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
    parser = argparse.ArgumentParser(prog="Configure mysqlgovernor limits with Control Panel Packages",
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
    _set = subparser.add_parser('set',
                               help='Set limits for governor packages limits',
                               description='Description: Set cpu limit for governor package')
    _set.add_argument('--package', help='Package name', type=str, required=True)
    _set.add_argument('--cpu', help='limit CPU (pct) usage', nargs='+',)
    _set.add_argument('--read', help='limit READ (MB/s) usage', nargs='+')
    _set.add_argument('--write', help='limit WRITE (MB/s) usage', nargs='+')
    _set.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ DELETE ################
    delete = subparser.add_parser('delete',
                                  help='Delete governor package limits',
                                  description='Description: Delete governor package limit',
                                  usage='governor_package_limitting.py delete [PACKAGE_NAME]')
    delete._optionals.title = 'Options'
    delete.add_argument('--package', help='Package name', type=str, required=True)
    delete.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ GET ################
    get = subparser.add_parser('get',
                               help='Get governor package limits',
                               description='Description: Get governor package limits',
                               usage='governor_package_limitting.py get [OPTIONS]',
                               formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=99999))
    get._optionals.title = 'Options'
    g = get.add_mutually_exclusive_group()
    g.add_argument('--package', help='Get package limits', type=str, )
    g.add_argument('--all', help="Get all package limits", action='store_true')

    get.add_argument('--format', help='Show limits in formats: (KB/s), (BB/s), (MB/s). Default is mb', default='mb',
                     choices=['bb', 'kb', 'mb'])

    get._optionals.title = 'Options'
    get.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ SYNC ################
    sync = subparser.add_parser('sync',
                                help='Synchronize governor package limits',
                                description='Description: Apply package limitting configuration to governor',
                                usage='governor_package_limitting.py sync')
    sync._optionals.title = 'Options'
    sync.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ SYNC WITH CPANEL ################
    sync_with_panel = subparser.add_parser('sync-with-panel',
                                help='Synchronize governor package limits with  Panel',
                                description='Description: Synchronize governor package limitting with Panel',
                                usage='governor_package_limitting.py sync-with-panel')
    sync_with_panel._optionals.title = 'Options'
    sync_with_panel.add_argument('--debug', action='store_true', help='Turn on debug mode')

    return parser


def cp_packages() -> Dict[str, list]:
    """
    Get packages and it's users.
    Returns:
        (dict): package_name and contained users list
    """
    __cpinfo = cpinfo()
    users_and_packages = {}
    for i in __cpinfo:
        if users_and_packages.get(i[1]):
            users_and_packages[i[1]].append(i[0])
        else:
            users_and_packages[i[1]] = [i[0]]
    return users_and_packages


def limits_serializer(args: List):
    """Serialize cli arguments
    From cli cpu read write options we receive as list['int']
    For example: ['1,2,3,4']
    Serialize will convert to the following: [1,2,3,4] or return None
    """
    __limits = []
    try:
        if args and isinstance(args, list):
            for i in args[0].split(','):
                __limits.append(i)
    except Exception as err:
        print(f'Some parameters are incorrect: {err}')
        sys.exit(1)

    if len(__limits) > 4:
        print(f'Some parameters are incorrect. Provided options is more than 4')
        sys.exit(1)

    if len(__limits) < 4:
        while len(__limits) < 4:
            __limits.append(-1)
    return __limits


def set_package_limits(package: str, cpu: list = None, io_read: List = None, io_write: list = None, serialize=True):
    """Setting package limits
    Args:
        package (str): Package name
        cpu (list): cpu limits
        io_read (list): io read limits
        io_write (list): io write limits
        serialize (bool): To serialize or not
    Return:
        None
    """

    cfg = {
        package: {
            'cpu': limits_serializer(cpu) if serialize else cpu,
            'read': limits_serializer(io_read) if serialize else io_read,
            'write': limits_serializer(io_write) if serialize else io_write,
        }
    }

    cfg = format_converter(cfg)

    if not os.path.exists(PACKAGE_LIMIT_CONFIG):
        debug_log(f'Creating file {PACKAGE_LIMIT_CONFIG} with content {cfg}')
        with open(PACKAGE_LIMIT_CONFIG, 'w') as ymlfile:
            yaml.dump(cfg, ymlfile)
        return

    config = get_package_limit()

    if not config:
        config = {}

    if config.get(package):
        for k in list(cfg[package]):
            if cfg.get(package)[k].count(-1) == 4:
                del cfg.get(package)[k]
        config[package] = {**config[package], **cfg[package]}
    else:
        config[package] = cfg[package]

    debug_log(f'Setting package limit with config: {config}')

    debug_log('\n')
    with open(PACKAGE_LIMIT_CONFIG, 'w') as ymlfile:
        yaml.dump(config, ymlfile)
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
        config.pop(package)
        with open(PACKAGE_LIMIT_CONFIG, 'w') as ymlfile:
            if config:
                yaml.dump(config, ymlfile)
                debug_log(f'Deleting package {package} from config')
    except (KeyError, AttributeError) as err:
        print(f'Package name {package} not found')
        debug_log(err)
        return


def get_package_limit(package: str = None, limit_format: str = 'mb', print_to_stdout=False):
    """Get package limits
    Args:
        package (str): name of package to get
        print_to_stdout (bool): Print to stdout is used for cli.
        limit_format: Print values in specified format. mb, kb, bb
    Returns:
        Package limit configurations or provided package configuration
    """
    if os.path.exists(PACKAGE_LIMIT_CONFIG):
        debug_log(f'Reading file {PACKAGE_LIMIT_CONFIG}')
        with open(PACKAGE_LIMIT_CONFIG, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            debug_log(f'config file content is: {cfg}')

    if cfg and package:
        cfg = cfg.get(package)
        if cfg:
            cfg = {package: cfg}

    if print_to_stdout and cfg:
        for key, val in cfg.items():
            for k, v in val.items():
                for i in range(4):
                    cfg[key][k][i] = format_calc(v[i], from_format='mb', to_format=limit_format)
        print(json.dumps(cfg))

    debug_log('\n')
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
            command = f'dbctl delete {user}'
            debug_log(f'Running command: {command}')
            subprocess.run(command, shell=True, text=True)

    if action == 'set' and limits and users:
        for user in users:
            cpu, io_read, io_write = prepare_limits(user, package_limit=limits)
            command = f'dbctl set {user} --cpu={cpu} --read={io_read} --write={io_write}'
            debug_log(f'Running command: {command}')
            subprocess.run(command, shell=True, text=True)
    debug_log('\n')


def dbctl_sync(action: str, package: str = None):
    """Sync package configuration with dbgovernor
    Args:
        action (str): Set or Delete
        package (str): Package name is used with action delete.
    """
    if not action:
        print("Action not specified")
        sys.exit(1)
    __cp_packages = cp_packages()

    if action == 'delete' and package:
        users_to_apply_package = __cp_packages.get(package)
        if users_to_apply_package:
            debug_log(f'Deleting package limits for users: {users_to_apply_package}')
            run_dbctl_command(users_to_apply_package, action)
            return

    if action == 'set':
        package_limits = get_package_limit()
        for package_name, limits in package_limits.items():
            users_to_apply_package = __cp_packages.get(package_name)
            if users_to_apply_package and package_name != 'default':
                debug_log(f'Setting package limits for users: {users_to_apply_package}')
                run_dbctl_command(users_to_apply_package, action, limits)

    users_to_apply_default_limits = __cp_packages.get('default')
    run_dbctl_command(users_to_apply_default_limits, 'delete')


def format_calc(value: int, from_format: str, to_format: str):
    """Converting integer between formats mb|kb|bb
    Args:
        value (int): Integer value to convert
        from_format (str): To convert from mb|kb|bb\
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

    value = ceil(value)
    return value


def format_converter(cfg: dict):
    """Converting bytes to MB
    Some parameters from user cli can be in bytes, for example [-1, 50, 52428800b, 100]
    52428800b is 50 MB
    Args:
        cfg (dict): {cpu: [x,x,x,x], read: [x,x,x,x], write: [x,x,x,x,]}
    Returns:
          cfg (dict)
    """
    if not cfg:
        return

    for key, val in cfg.items():
        for k, v in val.items():
            if k != 'cpu':
                for i in range(4):
                    if isinstance(v[i], str):
                        if 'b' in v[i]:
                            debug_log(f'Converting byte `{v[i]}` to MB')
                            v[i] = format_calc(
                                ceil(int(v[i].replace('b', ''))),
                                from_format='bb', to_format='mb'
                            )
                        else:
                            v[i] = int(v[i])
            else:
                for i in range(4):
                    v[i] = int(v[i])

    debug_log('\n')
    return cfg


def prepare_limits(user: str, package_limit: Dict) -> List:
    """Prepare Limits with algorithm
    Package name is pack1
    If value in pack1 is -1, look for in default limits. Default limit by default is -1
    If value in default limit is -1, apply individual limit from user
    For example:
    Pack1 Package limit for cpu is: [100, -1, 65, -1]
    Default Package limit is:       [-1, 90, -1, -1]
    Individual limit is:            [100, 200, 300 ,400]
    Result will be:                 [100, 90, 65, 400]
    Args:
        user (str): Get user's individual limits from dbctl
        package_limit: Package limits of cpu, read and write in dict format {'cpu': [1,1,1,1], 'read': [2,2,2,2], 'write': [3,3,3,3]}
    Returns:
        After performing logical calculation: ['1,1,1,1'], ['2,2,2,2'], ['3,3,3,3']
    """
    get_individual_limit_command = f'dbctl list | tail -n +2 | grep -i {user} | head -n1'
    output = subprocess.run(get_individual_limit_command, shell=True, text=True, capture_output=True)

    if not output.stdout:
        print(f'Couldn\'t  find limits for {user} in dbctl')
        debug_log(output.stderr)
        exit(1)

    output = output.stdout.split()
    debug_log(f'Output of command: {get_individual_limit_command} is: {output}')

    individual_cpu_limit = [int(i) for i in output[1].split('/')]
    individual_read_limit = [int(i) for i in output[2].split('/')]
    individual_write_limit = [int(i) for i in output[3].split('/')]
    debug_log(f'{user}\'s individual limits are: ', end='')
    debug_log(f'cpu: {individual_cpu_limit}, read: {individual_read_limit}, write: {individual_write_limit}')

    default_cpu_limit = DEFAULT_PACKAGE_LIMITS.get('cpu')
    default_read_limit = DEFAULT_PACKAGE_LIMITS.get('read')
    default_write_limit = DEFAULT_PACKAGE_LIMITS.get('write')

    package_cpu_limit = package_limit.get('cpu')
    package_read_limit = package_limit.get('read')
    package_write_limit = package_limit.get('write')

    cpu_limit = package_cpu_limit
    read_limit = package_read_limit
    write_limit = package_write_limit

    for i in range(4):
        if cpu_limit[i] < 0:
            cpu_limit[i] = default_cpu_limit[i]
            if cpu_limit[i] < 0:
                cpu_limit[i] = individual_cpu_limit[i]

        if read_limit[i] < 0:
            read_limit[i] = default_read_limit[i]
            if read_limit[i] < 0:
                read_limit[i] = individual_read_limit[i]

        if write_limit[i] < 0:
            write_limit[i] = default_write_limit[i]
            if write_limit[i] < 0:
                write_limit[i] = individual_write_limit[i]
    try:
        cpu = ','.join(str(x) for x in cpu_limit)
        io_read = ','.join(str(x) for x in read_limit)
        io_write = ','.join(str(x) for x in write_limit)
        debug_log(f'Limits after calculation for {user} is:')
        debug_log(f'cpu: [{cpu}], read: [{io_read}], write: [{io_write}]')
        return cpu, io_read, io_write
    except TypeError as err:
        print(f'Some limits are not given: {err}')
        sys.exit(1)


def sync_with_panel():
    # TODO MYSQLG-789
    """Syncing with panel
    For now we are just getting package names and applying default values.
    In future we will get packages with limits and apply it.
    """
    all_packages = admin_packages()
    for package in all_packages:
        if not get_package_limit(package):
            set_package_limits(
                package,
                DEFAULT_PACKAGE_LIMITS.get('cpu'),
                DEFAULT_PACKAGE_LIMITS.get('read'),
                DEFAULT_PACKAGE_LIMITS.get('write'),
                serialize=False
            )


def check_and_set_default_value():
    """Check for default limits are applied or not
    If default limits are not configured, then apply DEFAULT_PACKAGE_LIMITS [-1, -1, -1, -1] for cpu, read amd write
    """
    global DEFAULT_PACKAGE_LIMITS

    __default_limit = get_package_limit('default')
    if not __default_limit:
        set_package_limits(
            'default',
            DEFAULT_PACKAGE_LIMITS.get('cpu'),
            DEFAULT_PACKAGE_LIMITS.get('read'),
            DEFAULT_PACKAGE_LIMITS.get('write'),
            serialize=False
        )
    else:
        DEFAULT_PACKAGE_LIMITS = __default_limit.get('default')


def main(argv):
    """
    Run main actions
    """

    sys.stdout = Logger(sys.stdout, LOG_FILE_NAME)
    sys.stderr = Logger(sys.stderr, LOG_FILE_NAME)
    shadow_tracing(True)

    parser = build_parser()
    if not argv:
        parser.print_help()
        sys.exit(1)

    opts = parser.parse_args(argv)
    if opts.debug:
        global DEBUG
        DEBUG = True

    if not os.path.exists(PACKAGE_LIMIT_CONFIG):
        debug_log(f'Config file: {PACKAGE_LIMIT_CONFIG} not exists')
        debug_log(f'Creating config file: {PACKAGE_LIMIT_CONFIG}\n')
        with open(PACKAGE_LIMIT_CONFIG, 'w+'):
            pass
    debug_log("Checking for default value. If default limits are not configured, then apply default limits [-1]\n")
    check_and_set_default_value()

    if opts.command == 'set':
        set_package_limits(opts.package, opts.cpu, opts.read, opts.write)
        dbctl_sync('set')
    elif opts.command == 'get':
        get_package_limit(opts.package, opts.format, print_to_stdout=True)
    elif opts.command == 'delete':
        delete_package_limit(opts.package)
        dbctl_sync('delete', opts.package)
    elif opts.command == 'sync':
        dbctl_sync('set')
    elif opts.command == 'sync-with-panel':
        sync_with_panel()
    else:
        parser.print_help()
        sys.exit(1)


if "__main__" == __name__:
    main(sys.argv[1:])
