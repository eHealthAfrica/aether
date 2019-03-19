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

import json
import logging

from django.conf import settings
from django.utils.translation import ugettext as _

from .models import DeviceDB
from .couchdb_helpers import create_db, create_document


logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


def load_backup_file(fp):
    '''
    POST file content into CouchDB server.

    The Mobile App implements another way of synchronize documents, using backup files.
    In this case we are trying to simulate the Mobile App sync process.
    '''

    # read entries
    entries = json.load(fp)
    stats = {
        'total': 0,
        'success': 0,
        'erred': 0,
        'err_docs': [],
        'errors': {},
    }

    # each entry has a "deviceId" property
    # use it to create the linked DeviceDB along with the CouchDB user and database
    # {
    #     "id": "schema-1234",
    #     "key": "schema-1234",
    #     "value": {
    #         "rev": "1-xyz"
    #     },
    #     "doc": {
    #         "_id": "schema-1234",
    #         "_rev": "1-xyz",
    #         "deviceId": "abc9876",
    #         # ...
    #     }
    # }
    # ASSUMPTION: all entries belong to the same deviceId
    devices = [
        entry['doc']['deviceId']
        for entry in entries
        if 'deviceId' in entry['doc']
    ]
    device_id = devices[0] if devices else 'unknown'

    # Get/Create the device db record and couchdb db
    try:
        DeviceDB.objects.get(device_id=device_id)
    except DeviceDB.DoesNotExist:
        logger.debug(_('Creating db for device {}').format(device_id))
        DeviceDB.objects.create(device_id=device_id)

    # Create couchdb for device
    try:
        create_db(device_id)
    except Exception as err:
        logger.error(_('Creating couchdb db failed'))
        logger.exception(err)

    logger.debug(_('Processing {} documents...').format(len(entries)))

    for entry in entries:
        stats['total'] += 1
        doc = entry['doc']
        # FIXME: workaround to document conflict
        if '_rev' in doc:
            doc['mobile__rev'] = doc['_rev']
            del doc['_rev']

        # create document
        try:
            resp = create_document(device_id, doc)
            resp.raise_for_status()
            stats['success'] += 1

        except Exception as err2:
            stats['erred'] += 1
            stats['err_docs'].append(doc)
            stats['errors'][doc['_id']] = resp.json()

            logger.error(_('Error creating document {}. Reason: {}').format(
                doc['_id'],
                resp.json()['reason']
            ))
            logger.exception(err2)

    logger.debug(_('Processed {} documents.').format(stats['total']))

    return stats
