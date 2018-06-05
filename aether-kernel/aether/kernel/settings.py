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
from aether.common.conf.settings import INSTALLED_APPS, REST_FRAMEWORK

# Kernel Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.kernel.urls'
WSGI_APPLICATION = 'aether.kernel.wsgi.application'
ADD_REVERSION_ADMIN = True

INSTALLED_APPS += [
    'django_filters',
    'rest_framework_filters',
    'reversion',
    'reversion_compare',
    'aether.kernel',
    'drf_openapi',
]

MIGRATION_MODULES = {
    'kernel': 'aether.kernel.api.migrations'
}

REST_FRAMEWORK['DEFAULT_VERSIONING_CLASS'] = 'rest_framework.versioning.URLPathVersioning'
REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'] = (
    'rest_framework_filters.backends.DjangoFilterBackend',
) + REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS']
