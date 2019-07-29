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

# Common settings
# ------------------------------------------------------------------------------

import os

from aether.sdk.conf.settings_aether import *  # noqa
from aether.sdk.conf.settings_aether import (
    INSTALLED_APPS,
    MIGRATION_MODULES,
    PROFILING_ENABLED,
    REST_FRAMEWORK,
)

# Kernel Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.kernel.urls'

INSTALLED_APPS += [
    'django_filters',
    'drf_yasg',
]

MULTITENANCY_MODEL = 'kernel.Project'
MIGRATION_MODULES['kernel'] = 'aether.kernel.api.migrations'

REST_FRAMEWORK['DEFAULT_VERSIONING_CLASS'] = 'rest_framework.versioning.URLPathVersioning'
REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'] = [
    'django_filters.rest_framework.DjangoFilterBackend',
    *REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'],
]


# Export Configuration
# ------------------------------------------------------------------------------

EXPORT_CSV_ESCAPE = os.environ.get('EXPORT_CSV_ESCAPE', '\\')
EXPORT_CSV_QUOTE = os.environ.get('EXPORT_CSV_QUOTE', '"')
EXPORT_CSV_SEPARATOR = os.environ.get('EXPORT_CSV_SEPARATOR', ',')
EXPORT_DATA_FORMAT = os.environ.get('EXPORT_DATA_FORMAT', 'split')
EXPORT_HEADER_CONTENT = os.environ.get('EXPORT_HEADER_CONTENT', 'labels')
EXPORT_HEADER_SEPARATOR = os.environ.get('EXPORT_HEADER_SEPARATOR', '/')
EXPORT_HEADER_SHORTEN = os.environ.get('EXPORT_HEADER_SHORTEN', 'no')


# Profiling workaround
# ------------------------------------------------------------------------------
#
# Issue: The entities bulk creation is failing with Silk enabled.
# The reported bug, https://github.com/jazzband/django-silk/issues/348,
# In the meantime we will disable silk for those requests.

if PROFILING_ENABLED:
    def ignore_entities_post(request):
        return request.method != 'POST' or '/entities' not in request.path

    SILKY_INTERCEPT_FUNC = ignore_entities_post
