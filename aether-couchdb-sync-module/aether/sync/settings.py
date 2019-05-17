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

from aether.common.settings import *  # noqa
from aether.common.settings import MIGRATION_MODULES


# Sync Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.sync.urls'

# Allow cors for all origins but only for the sync endpoint
CORS_URLS_REGEX = r'^/sync/.*$'

# SECURITY WARNING: this should also be considered a secret:
GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']

FIXTURE_DIRS = (
    'aether/sync/fixtures/',
)

MULTITENANCY_MODEL = 'sync.Project'
MIGRATION_MODULES['sync'] = 'aether.sync.api.migrations'


# CouchDB Configuration
# ------------------------------------------------------------------------------

COUCHDB_URL = os.environ['COUCHDB_URL']
COUCHDB_USER = os.environ['COUCHDB_USER']
COUCHDB_PASSWORD = os.environ['COUCHDB_PASSWORD']
COUCHDB_DIR = os.environ.get('COUCHDB_DIR', './couchdb')
