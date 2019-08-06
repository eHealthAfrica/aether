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
# under the License.

import os
import logging


def get_required(name):
    try:
        return os.environ[name]
    except KeyError as key:
        raise RuntimeError(f'Missing {key} environment variable!')


DEBUG = bool(os.environ.get('DEBUG'))
TESTING = bool(os.environ.get('TESTING'))
SECRET_KEY = get_required('DJANGO_SECRET_KEY')

LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')

USE_I18N = True
USE_L10N = True
USE_TZ = True

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 0)
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
KERNEL_TOKEN = os.environ.get('AETHER_KERNEL_TOKEN', '')
KERNEL_URL = os.environ.get('AETHER_KERNEL_URL', '')
DEFAULT_REALM = os.environ.get('DEFAULT_REALM', 'aether')

LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', logging.INFO)
