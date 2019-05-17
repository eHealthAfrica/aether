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

import logging

from django.conf import settings
from django.utils.translation import ugettext as _

from . import api
from .. import errors
from .utils import force_put_doc


logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)

SYSTEM_DATABASES = [
    '_users',
    # '_replicator',
    # '_global_changes',
]


def setup_db(db_name, config, cleanup=False):  # pragma: no cover
    '''
    Setup up a couchdb database from a configuration,

    When `cleanup` is `True` all the data will be wiped from the existing database!
    '''

    ddoc = config.copy()
    # The {db}/_security is its own document in couchdb and we push it seperately.
    # A security document is required.
    if '_security' in config:
        secdoc = ddoc['_security']
        del ddoc['_security']
    else:
        raise errors.CouchDBInitializationError(
            _('Provide a security document for the couchdb: {}').format(db_name)
        )

    create_db(db_name, cleanup)

    if '_id' in ddoc:
        ddoc_url = db_name + '/' + ddoc['_id']
        force_put_doc(ddoc_url, ddoc)

    secdoc_url = db_name + '/_security'
    force_put_doc(secdoc_url, secdoc)


def create_db(db_name, cleanup=False):  # pragma: no cover
    r = api.get(db_name)
    exists = r.status_code < 400

    # In testing mode we delete existing couchdbs
    if exists and cleanup:
        logger.info(_('Deleting couchdb: {}').format(db_name))
        r = api.delete(db_name)
        r.raise_for_status()
        exists = False

    if not exists:
        logger.info(_('Creating couchdb: {}').format(db_name))
        r = api.put(db_name)
        r.raise_for_status()
