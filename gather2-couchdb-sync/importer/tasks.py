import logging
from django_rq import job
from importer.import_couchdb import import_synced_devices
from sync import settings

logger = logging.getLogger(__name__)


@job('default', timeout=15 * 60)
def import_synced_devices_task():
    try:
        settings.test_gather_core_connection()
        return import_synced_devices()
    except RuntimeError as re:
        logger.warning('Cannot connect to {}'.format(settings.GATHER_CORE_URL))

    return {}
