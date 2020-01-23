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


# Upload files
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-DATA_UPLOAD_MAX_MEMORY_SIZE
# https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-FILE_UPLOAD_MAX_MEMORY_SIZE

_max_size = 20 * 1000 * 1000  # 20MB
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', _max_size))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('FILE_UPLOAD_MAX_MEMORY_SIZE', _max_size))


# Export Configuration
# ------------------------------------------------------------------------------

EXPORT_CSV_ESCAPE = os.environ.get('EXPORT_CSV_ESCAPE') or '\\'
EXPORT_CSV_QUOTE = os.environ.get('EXPORT_CSV_QUOTE') or '"'
EXPORT_CSV_SEPARATOR = os.environ.get('EXPORT_CSV_SEPARATOR') or ','
EXPORT_DATA_FORMAT = os.environ.get('EXPORT_DATA_FORMAT', '').lower()
if EXPORT_DATA_FORMAT != 'flatten':
    EXPORT_DATA_FORMAT = 'split'
EXPORT_HEADER_CONTENT = os.environ.get('EXPORT_HEADER_CONTENT', '').lower()
if EXPORT_HEADER_CONTENT not in ('labels', 'paths', 'both'):
    EXPORT_HEADER_CONTENT = 'labels'
EXPORT_HEADER_SEPARATOR = os.environ.get('EXPORT_HEADER_SEPARATOR') or '/'
EXPORT_HEADER_SHORTEN = os.environ.get('EXPORT_HEADER_SHORTEN', '').lower()
if EXPORT_HEADER_SHORTEN != 'yes':
    EXPORT_HEADER_SHORTEN = 'no'

try:
    EXPORT_NUM_CHUNKS = int(os.environ.get('EXPORT_NUM_CHUNKS', 4))
except ValueError:
    EXPORT_NUM_CHUNKS = 4
if EXPORT_NUM_CHUNKS < 1:
    EXPORT_NUM_CHUNKS = 1


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


# Swagger workaround
# ------------------------------------------------------------------------------
# The ``bravado`` lib in ``aether.client`` cannot deal with JSON fields handled
# as objects, so we need to remove the ``JSONFieldInspector`` class
# and continue using the ``StringDefaultFieldInspector`` one for them.

SWAGGER_SETTINGS = {
    # https://drf-yasg.readthedocs.io/en/stable/settings.html#default-field-inspectors
    'DEFAULT_FIELD_INSPECTORS': [
        'drf_yasg.inspectors.CamelCaseJSONFilter',
        'drf_yasg.inspectors.ReferencingSerializerInspector',
        'drf_yasg.inspectors.RelatedFieldInspector',
        'drf_yasg.inspectors.ChoiceFieldInspector',
        'drf_yasg.inspectors.FileFieldInspector',
        'drf_yasg.inspectors.DictFieldInspector',
        # Remove JSONFieldInspector
        # 'drf_yasg.inspectors.JSONFieldInspector',
        'drf_yasg.inspectors.HiddenFieldInspector',
        'drf_yasg.inspectors.RecursiveFieldInspector',
        'drf_yasg.inspectors.SerializerMethodFieldInspector',
        'drf_yasg.inspectors.SimpleFieldInspector',
        'drf_yasg.inspectors.StringDefaultFieldInspector',
    ],
}
