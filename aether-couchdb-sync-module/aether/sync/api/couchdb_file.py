import json
import logging

from .models import DeviceDB
from .couchdb_helpers import create_db, create_or_update_user, create_document
from ..settings import LOGGING_LEVEL


logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)


def load_file(fp):
    '''
    POST file content into CouchDB server.

    The Mobile App implements another way of synchronize documents, using backup files.
    In this case we are trying to simulate the Mobile App sync process.
    '''

    # read entries
    documents = json.load(fp)
    devices = set()
    stats = {
        'total': 0,
        'success': 0,
        'erred': 0,
        'err_docs': [],
    }

    logger.info(_('Processing {} documents...').format(len(documents)))

    for doc in documents:
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
                stats['erred'] += 1
                stats['err_docs'].push(doc)

                logger.exception(err)
                logger.error(_('Creating couchdb db failed'))
                continue

        # create document
        try:
            r = create_document(device_id, doc)
            r.raise_for_status()
            stats['success'] += 1

        except Exception as ce:
            stats['erred'] += 1
            stats['err_docs'].push(doc)

            logger.error(_('Error creating document {}.').format(doc['_id']))
            logger.exception(e)

    logger.info(_('Processed {} documents.').format(stats['total']))

    return stats
