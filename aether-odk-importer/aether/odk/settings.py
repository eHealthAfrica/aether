# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS


# ODK Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.odk.urls'
WSGI_APPLICATION = 'aether.odk.wsgi.application'

# Allow cors for all origins but only for the submission endpoint
CORS_URLS_REGEX = r'^/submission/.*$'

INSTALLED_APPS += [
    'aether.odk',
]

MIGRATION_MODULES = {
    'odk': 'aether.odk.api.migrations',
}
