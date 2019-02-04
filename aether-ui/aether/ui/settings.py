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

# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS, STATIC_ROOT


# UI Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.ui.urls'

# Javascript/CSS Files:
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': '/',
        'STATS_FILE': os.path.join(STATIC_ROOT, 'webpack-stats.json'),
        'POLL_INTERVAL': 0.1,  # in miliseconds
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
