from importer.import_couchdb import import_synced_devices
from django_rq import job


@job('default', timeout=15 * 60)
def import_synced_devices_task():
    return import_synced_devices()
