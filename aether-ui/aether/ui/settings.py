# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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

# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS, STATIC_ROOT


# UI Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.ui.urls'
DEBUG = bool(os.environ.get('DEBUG'))
LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)

WEBPACK_STATS_FILE = os.environ.get(
    'WEBPACK_STATS_FILE',
    os.path.join(STATIC_ROOT, 'webpack-stats.json')
)
logger.debug(f'Assets served by file:  {WEBPACK_STATS_FILE}')

# Javascript/CSS Files:
# https://github.com/owais/django-webpack-loader#default-configuration
WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': '/',
        'STATS_FILE': WEBPACK_STATS_FILE,
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': [r'.+\.hot-update.js', r'.+\.map'],
    },
}

INSTALLED_APPS += [
    'webpack_loader',
    'aether.ui',
]

MIGRATION_MODULES = {
    'ui': 'aether.ui.api.migrations'
}
