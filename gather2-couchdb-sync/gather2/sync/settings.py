import os

# Common settings
# ------------------------------------------------------------------------------

from gather2.common.conf.settings import *  # noqa
from gather2.common.conf.settings import INSTALLED_APPS


# Sync Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'gather2.sync.urls'
WSGI_APPLICATION = 'gather2.sync.wsgi.application'

# Allow cors for all origins but only for the sync endpoint
CORS_URLS_REGEX = r'^/sync/.*$'

# SECURITY WARNING: this should also be considered a secret:
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')

FIXTURE_DIRS = (
    'gather2/sync/fixtures/',
)

INSTALLED_APPS += [
    'django_rq',
    'gather2.sync',
]

MIGRATION_MODULES = {
    'sync': 'gather2.sync.api.migrations',
}

COUCHDB_URL = os.environ.get('COUCHDB_URL', 'http://couchdb:5984')
COUCHDB_USER = os.environ.get('COUCHDB_USER', None)
COUCHDB_PASSWORD = os.environ.get('COUCHDB_PASSWORD', None)
COUCHDB_DIR = './couchdb'

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 0)
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

RQ_QUEUES = {
    'default': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': REDIS_DB,
        'PASSWORD': REDIS_PASSWORD,
        'DEFAULT_TIMEOUT': 360,
    },
}
RQ_SHOW_ADMIN_LINK = True
