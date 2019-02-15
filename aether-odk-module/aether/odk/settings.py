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

# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import (
    INSTALLED_APPS,
    MIGRATION_MODULES,
    check_storage,
)


# ODK Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.odk.urls'

# Allow cors for all origins but only for the submission endpoint
CORS_URLS_REGEX = r'^/submission/.*$'

INSTALLED_APPS += [
    'aether.odk',
]

# In case of Mutitenancy is enabled!
MULTITENANCY_MODEL = 'odk.Project'
MIGRATION_MODULES['odk'] = 'aether.odk.api.migrations'


# Storage Configuration
# ------------------------------------------------------------------------------
check_storage()
