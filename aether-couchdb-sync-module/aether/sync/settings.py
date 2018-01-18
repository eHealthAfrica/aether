import os
import srvlookup

# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS


# Sync Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.sync.urls'
WSGI_APPLICATION = 'aether.sync.wsgi.application'

# Allow cors for all origins but only for the sync endpoint
CORS_URLS_REGEX = r'^/sync/.*$'

# SECURITY WARNING: this should also be considered a secret:
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')

FIXTURE_DIRS = (
    'aether/sync/fixtures/',
)

INSTALLED_APPS += [
    'django_rq',
    'aether.sync',
]

MIGRATION_MODULES = {
    'sync': 'aether.sync.api.migrations',
}

COUCHDB_URL = os.environ.get('COUCHDB_URL', 'http://couchdb:5984')
COUCHDB_USER = os.environ.get('COUCHDB_USER', None)
COUCHDB_PASSWORD = os.environ.get('COUCHDB_PASSWORD', None)
COUCHDB_DIR = './couchdb'

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 0)
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)


# Used only in deployment
current_environment = os.environ.get('ENV', '')
if current_environment in ('dev', 'staging', 'prod'):  # pragma: no cover
    domain = 'eha.{env}.local'.format(env=current_environment)
    project = os.environ.get('PROJECT', 'aether')

    try:
        # get dynamic Redis host/port
        redis = 'redis.{project}'.format(project=project)
        redis_host = srvlookup.lookup(redis, domain=domain)
        REDIS_HOST = redis_host[0][0]
        REDIS_PORT = redis_host[0][1]
    except Exception as e:
        # use default values
        pass

    try:
        # get dynamic CouchDB URL
        couchdb = 'couchdb.{project}'.format(project=project)
        couchdb_host = srvlookup.lookup(couchdb, domain=domain)
        COUCHDB_URL = 'http://{host}:{port}'.format(
            host=couchdb_host[0][0],
            port=couchdb_host[0][1]
        )
    except Exception as e:
        # use default value
        pass


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
