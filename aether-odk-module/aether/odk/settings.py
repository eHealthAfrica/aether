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

# Common settings
# ------------------------------------------------------------------------------

from aether.sdk.conf.settings_aether import *  # noqa
from aether.sdk.conf.settings_aether import MIGRATION_MODULES


# ODK Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.odk.urls'

# Allow cors for all origins but only for the submission endpoint
CORS_URLS_REGEX = r'^/submission/.*$'

MULTITENANCY_MODEL = 'odk.Project'
MIGRATION_MODULES['odk'] = 'aether.odk.api.migrations'

SURVEYOR_GROUP_NAME = 'surveyor'

ODK_COLLECT_ENDPOINT = os.environ.get('ODK_COLLECT_ENDPOINT', '')


# Upload files
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-DATA_UPLOAD_MAX_MEMORY_SIZE
# https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-FILE_UPLOAD_MAX_MEMORY_SIZE

_max_size = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', _max_size))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('FILE_UPLOAD_MAX_MEMORY_SIZE', _max_size))
