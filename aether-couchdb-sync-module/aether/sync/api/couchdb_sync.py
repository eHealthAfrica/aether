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

import re
import requests

from django.utils import timezone
from django.utils.translation import ugettext as _

from aether.common.kernel import utils as kernel_utils

from .models import DeviceDB, Schema
from ..couchdb import utils, api
from ..settings import logger
from .. import errors


SYNC_DOC = 'sync_doc'


def write_meta_doc(db_name, aether_submission, doc, error=''):
    meta_doc = get_meta_doc(db_name, doc['_id'])
    sync_status_url = '{}/{}-synced'.format(db_name, doc['_id'])

    # Rather than writing aether id etc on a doc,
    # we add a separate META doc
    # this way, we don't create conflicts if the client updates the mapping submission
    meta_doc['type'] = SYNC_DOC
    # We can use linked docs to get the full docs in a couchdb view:
    meta_doc['main_doc_id'] = doc['_id']
    meta_doc['time'] = timezone.now().isoformat()

    if error:
        meta_doc['error'] = error
    else:
        meta_doc['last_rev'] = doc['_rev']
        meta_doc['aether_id'] = aether_submission['id']
        meta_doc.pop('error', None)  # remove any error annotations

    return api.put(sync_status_url, json=meta_doc)


def get_meta_doc(db_name, couchdb_id):
    sync_status_url = '{}/{}-synced'.format(db_name, couchdb_id)
    resp = api.get(sync_status_url)

    if resp.status_code == 200:
        return resp.json()

    return {}


def is_design_doc(doc):
    return re.match('^_design', doc['_id'])


def is_sync_doc(doc):
    return doc.get('type') == SYNC_DOC


def import_synced_devices():
    results = []

    for device in DeviceDB.objects.all():
        result = {
            'typename': 'synced data',
            'error': None,
            'stats': None
        }
        stats = None

        try:
            data = utils.fetch_db_docs(device.db_name, device.last_synced_seq)
            docs = data['docs']
            stats = import_synced_docs(docs, device.db_name)
            result['stats'] = stats
        except Exception as e:
            logger.exception(e)
            result['error'] = e
        else:
            logger.info('imported %s', device.device_id)
            device.last_synced_log_status = 'success'
            device.last_synced_seq = data['last_seq']
            device.last_synced_log_message = '{} - {} - {} - {}'.format(
                stats['total'],
                stats['created'],
                stats['updated'],
                stats['deleted'],
            )

        results.append(result)
        if (stats) and (stats['total'] > 0):
            device.last_synced_date = timezone.now()
            device.save()

    return results


def import_synced_docs(docs, db_name):
    stats = {
        'total': len(docs),
        'created': 0,
        'updated': 0,
        'errors': [],
        'deleted': 0,
        'errored': 0,
        'non-survey': 0,
        'up-to-date': 0,
    }

    for doc in docs:
        if is_design_doc(doc) or is_sync_doc(doc):
            stats['non-survey'] += 1
            continue

        # check sync status
        status = get_meta_doc(db_name, doc['_id'])
        if status.get('last_rev') == doc['_rev']:
            stats['up-to-date'] += 1
            continue

        aether_id = status.get('aether_id') or False

        try:
            resp = post_to_aether(doc, aether_id=aether_id)
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logger.error('post survey to aether failed: ' + resp.text)
                stats['errors'].append(resp.content)
                stats['errored'] += 1
                resp = write_meta_doc(db_name, {}, doc, error=resp.text)
                resp.raise_for_status()
                continue

            data = resp.json()

            resp = write_meta_doc(db_name, data, doc)
            resp.raise_for_status()

            if aether_id:
                stats['updated'] += 1
            else:
                stats['created'] += 1

        except Exception as e:
            logger.exception(e)
            stats['errors'].append(str(e))
            stats['errored'] += 1
            resp = write_meta_doc(db_name, {}, doc, error=str(e))
            resp.raise_for_status()

    if stats['errored'] > 0:
        raise errors.SubmissionError(stats['errors'][0])

    return stats


def post_to_aether(document, aether_id=False):
    # first of all check if the connection is possible
    if not kernel_utils.test_connection():
        raise RuntimeError(_('Cannot connect to Aether Kernel server'))

    try:
        schema_name = document['_id'].split('-')[0]
    except Exception:
        raise errors.SubmissionMappingError(
            _('Cannot submit document "{}"').format(document['_id'])
        )

    try:
        schema = Schema.objects.get(name=schema_name)
    except Schema.DoesNotExist:
        raise errors.SubmissionMappingError(
            _('Cannot submit document with schema "{}"').format(schema_name)
        )

    return kernel_utils.submit_to_kernel(submission=document,
                                         mapping_id=str(schema.kernel_id),
                                         submission_id=aether_id)
