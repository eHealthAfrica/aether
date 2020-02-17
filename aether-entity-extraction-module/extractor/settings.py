# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.d ~

import os
import json
import logging


def get_required(name):
    try:
        return os.environ[name]
    except KeyError:
        raise RuntimeError(f'Missing {name} environment variable!')


# Redis server
REDIS_HOST = get_required('REDIS_HOST')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')

# Aether kernel
KERNEL_TOKEN = get_required('AETHER_KERNEL_TOKEN')
KERNEL_URL = get_required('AETHER_KERNEL_URL')

# Multitenancy
DEFAULT_REALM = os.environ.get('DEFAULT_REALM', 'eha')
REALM_COOKIE = os.environ.get('REALM_COOKIE', 'eha-realm')

# Extractor settings
SUBMISSION_CHANNEL = os.environ.get('SUBMISSION_CHANNEL', '_submissions*')
WAIT_INTERVAL = float(os.environ.get('WAIT_INTERVAL', 1.0))  # in seconds
MAX_PUSH_SIZE = int(os.environ.get('MAX_PUSH_SIZE', 40))
LOCK_TIMEOUT = int(os.environ.get('LOCK_TIMEOUT', 60))

# https://docs.python.org/3.7/library/logging.html#levels
LOG_LEVEL = os.environ.get('LOGGING_LEVEL', 'DEBUG')


class StackdriverFormatter(logging.Formatter):
    # https://blog.frank-mich.com/python-logging-to-stackdriver/

    def __init__(self, *args, **kwargs):
        super(StackdriverFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        return json.dumps({
            'severity': record.levelname,
            'message': record.getMessage(),
            'name': record.name
        })


def get_logger(name):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(f'%(asctime)s [{name}] %(levelname)-8s %(message)s'))
    if str(os.environ.get('stackdriver_logging', True)) in ('yes', 'true', 't', '1', True):
        handler.setFormatter(StackdriverFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            f'%(asctime)s [{name}] %(levelname)-8s %(message)s'))
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.getLevelName(LOG_LEVEL))
    return logger
