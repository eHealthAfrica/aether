from django_rq import job
from importer.import_couchdb import import_synced_devices
from api import core_utils


@job('default', timeout=15 * 60)
def import_synced_devices_task():
    if core_utils.test_connection():
        return import_synced_devices()
    return {}
