from django_rq import job

from gather2.common.core.utils import test_connection
from .import_couchdb import import_synced_devices


@job('default', timeout=15 * 60)
def import_synced_devices_task():
    if test_connection():
        return import_synced_devices()
    return {}
