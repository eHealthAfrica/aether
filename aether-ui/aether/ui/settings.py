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

from aether.common.settings import *  # noqa
from aether.common.settings import (
    DEBUG,
    INSTALLED_APPS,
    LOGGING_LEVEL,
    MIGRATION_MODULES,
    STATIC_ROOT,
)

logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)


# UI Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.ui.urls'

INSTALLED_APPS += ['aether.ui', ]

MULTITENANCY_MODEL = 'ui.Project'
MIGRATION_MODULES['ui'] = 'aether.ui.api.migrations'

DEFAULT_PROJECT_NAME = os.environ.get('DEFAULT_PROJECT_NAME', 'AUX')
logger.debug(f'Default project name:  {DEFAULT_PROJECT_NAME}')
