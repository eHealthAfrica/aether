# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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
# under the License.

import os
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
PULL_INTERVAL = float(os.environ.get('PULL_INTERVAL', 3600))  # 1 hour
PULL_ENDPOINT = os.environ.get('PULL_ENDPOINT', 'admin/~extract?delta=1d')


# https://docs.python.org/3.7/library/logging.html#levels
LOG_LEVEL = os.environ.get('LOGGING_LEVEL', 'INFO')


def get_logger(name):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(f'%(asctime)s [{name}] %(levelname)-8s %(message)s'))

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.getLevelName(LOG_LEVEL))
    return logger


def _get_file_content(path, on_error):  # pragma: no cover
    try:
        with open(path) as fp:
            value = fp.read().strip()
    except Exception:
        value = on_error
    return value


# Version and revision
# ------------------------------------------------------------------------------

VERSION = _get_file_content('/var/tmp/VERSION', '#.#.#')
REVISION = _get_file_content('/var/tmp/REVISION', '---')
