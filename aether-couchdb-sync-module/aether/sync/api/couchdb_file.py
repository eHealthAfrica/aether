import json
import logging

from django.utils.translation import ugettext as _

from .models import DeviceDB
from .couchdb_helpers import create_db, create_document
from ..settings import LOGGING_LEVEL


logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)


def load_backup_file(fp):
    '''
    POST file content into CouchDB server.

    The Mobile App implements another way of synchronize documents, using backup files.
    In this case we are trying to simulate the Mobile App sync process.
    '''

    # read entries
    entries = json.load(fp)
    devices = set()
    stats = {
        'total': 0,
        'success': 0,
        'erred': 0,
        'err_docs': [],
        'errors': {},
    }

    logger.info(_('Processing {} documents...').format(len(entries)))

    for entry in entries:
        doc = entry['doc']
        stats['total'] += 1

        # each entry has a "deviceId" property, use it to create the linked DeviceDB
        # along with the CouchDB user and database
        device_id = doc['deviceId']
        if device_id not in devices:  # do this only once per device
            # Get/Create the device db record and couchdb db
            try:
                DeviceDB.objects.get(device_id=device_id)
            except DeviceDB.DoesNotExist:
                logger.info(_('Creating db for device {}').format(device_id))
                DeviceDB.objects.create(device_id=device_id)

            # Create couchdb for device
            try:
                create_db(device_id)
                devices.add(device_id)

            except Exception as err:
                logger.error(_('Creating couchdb db failed'))
                logger.exception(err)

        # create document
        try:
            resp = create_document(device_id, doc)
            resp.raise_for_status()
            stats['success'] += 1

        except Exception as err2:
            stats['erred'] += 1
            stats['err_docs'].append(doc)
            stats['errors'][doc['_id']] = resp.json()

            logger.error(_('Error creating document {}.').format(doc['_id']))
            logger.error(resp.content)
            logger.exception(err2)

    logger.info(_('Processed {} documents.').format(stats['total']))

    return stats
