# Common settings
# ------------------------------------------------------------------------------

from gather2.common.conf.settings import *  # noqa
from gather2.common.conf.settings import INSTALLED_APPS


# ODK Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'gather2.odk.urls'
WSGI_APPLICATION = 'gather2.odk.wsgi.application'

# Allow cors for all origins but only for the submission endpoint
CORS_URLS_REGEX = r'^/submission/.*$'

INSTALLED_APPS += [
    'gather2.odk',
]

MIGRATION_MODULES = {
    'odk': 'gather2.odk.api.migrations',
}
