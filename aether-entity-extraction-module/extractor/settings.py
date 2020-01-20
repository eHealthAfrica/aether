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


DEBUG = bool(os.environ.get('DEBUG'))
TESTING = bool(os.environ.get('TESTING'))

# Redis server
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 0)
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')

# Aether kernel
KERNEL_URL = os.environ.get('AETHER_KERNEL_URL', '')
KERNEL_TOKEN = os.environ.get('AETHER_KERNEL_TOKEN', '')

# Multitenancy
DEFAULT_REALM = os.environ.get('DEFAULT_REALM', '-')
REALM_COOKIE = os.environ.get('REALM_COOKIE')
GATEWAY_PUBLIC_REALM = os.environ.get('GATEWAY_PUBLIC_REALM', '-')

# Extractor settings
PUSH_TO_KERNEL_INTERVAL = float(os.environ.get('PUSH_TO_KERNEL_INTERVAL', 0.05))
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 10))
MAX_PUSH_SIZE = int(os.environ.get('MAX_PUSH_SIZE', 100))


# https://docs.python.org/3.7/library/logging.html#levels
LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', logging.INFO)
