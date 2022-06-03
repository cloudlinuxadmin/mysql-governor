# coding:utf-8

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT
#
"""
Init module
"""

from utilities import is_ubuntu
from .base import InstallManager
from .storage import Storage

if is_ubuntu():
    from .base_ubuntu import UbuntuInstallManager

