import os

# Common settings
# ------------------------------------------------------------------------------

from gather2.common.conf.settings import *  # noqa
from gather2.common.conf.settings import INSTALLED_APPS, TEMPLATES, TESTING, STATIC_ROOT


# UI Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'gather2.ui.urls'
WSGI_APPLICATION = 'gather2.ui.wsgi.application'

APP_NAME = 'Gather'
ORG_NAME = os.environ.get('GATHER_ORG_NAME', 'eHealth Africa')

DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

# Javascript/CSS Files:
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': '/',  # used in prod
        'STATS_FILE': os.path.join(STATIC_ROOT, 'webpack-stats.json'),
    },
}

INSTALLED_APPS += [
    'webpack_loader',
    'gather2.ui',
]

TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'gather2.ui.context_processors.gather2',
]

# MIGRATION_MODULES = {
#     'ui': 'gather2.ui.migrations'
# }

# check the available modules linked to this instance
GATHER_MODULES = os.environ.get('GATHER_MODULES', '').split(',')

GATHER_CORE_TOKEN = os.environ.get('GATHER_CORE_TOKEN')
if TESTING:  # pragma: no cover
    GATHER_CORE_URL = os.environ.get('GATHER_CORE_URL_TEST')
else:  # pragma: no cover
    GATHER_CORE_URL = os.environ.get('GATHER_CORE_URL')

# check if ODK is available in this instance
GATHER_ODK = ('odk-importer' in GATHER_MODULES)
if GATHER_ODK:  # pragma: no cover
    GATHER_ODK_TOKEN = os.environ.get('GATHER_ODK_TOKEN')
    if TESTING:
        GATHER_ODK_URL = os.environ.get('GATHER_ODK_URL_TEST')
    else:
        GATHER_ODK_URL = os.environ.get('GATHER_ODK_URL')
