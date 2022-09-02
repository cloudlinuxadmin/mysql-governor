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
from clcommon.cpapi import cpinfo
from typing import Dict, List
import yaml
import subprocess

LOG_FILE_NAME = "/usr/share/lve/dbgovernor/governor_package_limitting.log"
PACKAGE_LIMIT_CONFIG = '/etc/container/governor_package_limit.yaml'
DEBUG = False


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

    ################ UPDATE ################
    update = subparser.add_parser('update',
                                  help='Update limits for governor packages limits',
                                  description='Description: Update cpu limit for governor package',
                                  usage='governor_package_limitting.py update --package [PACKAGE_NAME] [OPTIONS]')
    update._optionals.title = 'Options'
    update.add_argument('--package', help='Package name', type=str, required=True)
    update.add_argument('--cpu', help='limit CPU (pct) usage', nargs='+',)
    update.add_argument('--read', help='limit READ (MB/s) usage', nargs='+')
    update.add_argument('--write', help='limit WRITE (MB/s) usage', nargs='+')
    update.add_argument('--debug', action='store_true', help='Turn on debug mode')

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
                               usage='governor_package_limitting.py get [OPTIONS]',)
    get._optionals.title = 'Options'
    g = get.add_mutually_exclusive_group()
    g.add_argument('--package', help='Get package limits', type=str, )
    g.add_argument('--all', help="Get all package limits", action='store_true')
    get._optionals.title = 'Options'
    get.add_argument('--debug', action='store_true', help='Turn on debug mode')

    ################ SYNC ################
    sync = subparser.add_parser('sync',
                                help='Synchronize governor package limits',
                                description='Description: Apply package limitting configuration to governor',
                                usage='governor_package_limitting.py sync')
    sync._optionals.title = 'Options'
    sync.add_argument('--debug', action='store_true', help='Turn on debug mode')

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
                __limits.append(int(i))
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


def set_package_limits(package: str, cpu: list = None, io_read: List = None, io_write: list = None):
    """Setting package limits
    If package exists return message about existence and suggest to update.
    Args:
        package (str): Package name
        cpu: (list): cpu limits
        io_read: (list): io read limits
        io_write: (list): io write limits
    Return:
        None
    """
    cfg = {
        package: {
            'cpu': limits_serializer(cpu),
            'read': limits_serializer(io_read),
            'write': limits_serializer(io_write),
        }
    }

    if not os.path.exists(PACKAGE_LIMIT_CONFIG):
        debug_log(f'Creating file {PACKAGE_LIMIT_CONFIG} with content {cfg}')
        with open(PACKAGE_LIMIT_CONFIG, 'w') as ymlfile:
            yaml.dump(cfg, ymlfile)
        dbctl_sync('set')
        sys.exit(0)

    config = get_package_limit()

    if not config:
        config = {}

    config[package] = cfg[package]
    print(f'Setting package limit with config: {config}')

    with open(PACKAGE_LIMIT_CONFIG, 'w') as ymlfile:
        yaml.dump(config, ymlfile)
        dbctl_sync('set')
        sys.exit(0)


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
            dbctl_sync('delete', package)
    except (KeyError, AttributeError) as err:
        print(f'Package name {package} not found: {err}')
        sys.exit(1)


def get_package_limit(package: str = None, print_to_stdout=False):
    """Get package limits
    Args:
        package (str): name of package to get
        print_to_stdout (bool): Print to stdout is used for cli.
    Returns:
        Package limit configurations or provided package configuration
    """
    if os.path.exists(PACKAGE_LIMIT_CONFIG):
        debug_log(f'Reading file {PACKAGE_LIMIT_CONFIG}')
        with open(PACKAGE_LIMIT_CONFIG, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
    if package:
        try:
            return cfg.get(package)
        except AttributeError as err:
            print(f'Package name {package} not found: {err}')
    if print_to_stdout and cfg:
        print(cfg)
    return cfg


def run_dbctl_command(users: list, action: str, limits: list = None):
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
        try:
            cpu = ','.join(str(x) for x in limits.get('cpu'))
            io_read = ','.join(str(x) for x in limits.get('read'))
            io_write = ','.join(str(x) for x in limits.get('write'))
        except TypeError as err:
            print(f'Some limits are not given: {err}')
            sys.exit(1)

        command = f'dbctl set {" ".join(users)} --cpu={cpu} --read={io_read} --write={io_write}'
        debug_log(f'Running command: {command}')
        subprocess.run(command, shell=True, text=True)


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
            sys.exit(0)

    if action == 'set':
        package_limits = get_package_limit()
        for package_name, limits in package_limits.items():
            users_to_apply_package = __cp_packages.get(package_name)
            if users_to_apply_package:
                debug_log(f'Setting package limits for users: {users_to_apply_package}')
                run_dbctl_command(users_to_apply_package, action, limits)


def debug_log(line):
    """
    Debug output log
    """
    global DEBUG
    if DEBUG:
        print(line)


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

    if opts.command == 'set':
        set_package_limits(opts.package, opts.cpu, opts.read, opts.write)
    elif opts.command == 'get':
        get_package_limit(opts.package, print_to_stdout=True)
    elif opts.command == 'delete':
        delete_package_limit(opts.package)
    elif opts.command == 'sync':
        dbctl_sync('set')
    else:
        parser.print_help()
        sys.exit(1)


if "__main__" == __name__:
    main(sys.argv[1:])
