import logging
import requests
import json
import re

from sync import settings
from django.utils import timezone
from couchdb_tools import utils, api
from api.models import DeviceDB

logger = logging.getLogger(__name__)

# survey_ids = {'building': 2, 'village': 3}
headers = {'Authorization': 'Token {}'.format(settings.GATHER_CORE_TOKEN),
           'Content-Type': 'application/json'}

SYNC_DOC = 'sync_doc'


def write_meta_doc(db_name, gather_response, doc, error=''):
    meta_doc = get_meta_doc(db_name, doc['_id'])
    sync_status_url = '{}/{}-synced'.format(db_name, doc['_id'])

    # Rather than writing gather id etc on a doc,
    # we add a separate META doc
    # this way, we don't create conflicts if the client updates the survey response
    meta_doc['type'] = SYNC_DOC
    # We can use linked docs to get the full docs in a couchdb view:
    meta_doc['main_doc_id'] = doc['_id']
    meta_doc['time'] = timezone.now().isoformat()

    if error:
        meta_doc['error'] = error
    else:
        meta_doc['last_rev'] = doc['_rev']
        meta_doc['gather_id'] = gather_response['id']
        meta_doc.pop('error', None)  # remove any error annotations

    return api.put(sync_status_url, json=meta_doc)


def get_meta_doc(db_name, couchdb_id):
    sync_status_url = '{}/{}-synced'.format(db_name, couchdb_id)
    resp = api.get(sync_status_url)

    if resp.status_code == 200:
        return resp.json()

    return {}


def get_survey_mapping():
    resp = requests.get('{}/surveys/'.format(settings.GATHER_CORE_URL), headers=headers).json()
    results = resp['results']

    # Pagination: seems like we do 30 per page
    # Loop through all the pages
    while resp['next']:
        resp = requests.get(resp['next'], headers=headers).json()
        results += resp['results']

    mapping = {}
    for survey in results:
        if not mapping.get(survey['name']):
            mapping[survey['name']] = survey['id']
    return mapping


def is_design_doc(doc):
    return re.match('^_design', doc['_id'])


def is_sync_doc(doc):
    return doc.get('type') == SYNC_DOC


def import_synced_devices():
    mapping = get_survey_mapping()
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
            stats = import_synced_docs(docs, device.db_name, mapping)
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


def import_synced_docs(docs, db_name, mapping):
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

        gather_id = status.get('gather_id') or False

        try:
            resp = post_to_gather(doc, mapping, gather_id=gather_id)

            if resp.status_code != 201 and resp.status_code != 200:
                stats['errors'].append(resp.content)
                write_meta_doc(db_name, {}, doc, error=resp.text)
                continue

            data = resp.json()
            write_meta_doc(db_name, data, doc)

            if gather_id is not None:
                stats['updated'] += 1
            else:
                stats['created'] += 1

        except Exception as e:
            write_meta_doc(db_name, {}, doc, error=str(e))
            stats['errors'].append(str(e))
            stats['errored'] += 1

    return stats


def post_to_gather(document, mapping, gather_id=False):
    prefix = document['_id'].split("-")[0]
    survey_id = mapping.get(prefix)

    if survey_id is None:
        raise Exception('no matching id for prefix {}'.format(prefix))

    if gather_id:
        # update existing doc
        url = '{}/surveys/{}/responses/{}/'.format(settings.GATHER_CORE_URL, survey_id, gather_id)
        return requests.put(url,
                            json={'data': json.dumps(document),
                                  'survey': survey_id},
                            headers=headers)

    url = '{}/surveys/{}/responses/'.format(settings.GATHER_CORE_URL, survey_id)
    return requests.post(url,
                         json={'data': json.dumps(document),
                               'survey': survey_id},
                         headers=headers)
