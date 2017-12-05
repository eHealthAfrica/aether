import os

# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS, TEMPLATES, TESTING, STATIC_ROOT


# UI Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.ui.urls'
WSGI_APPLICATION = 'aether.ui.wsgi.application'

APP_NAME = 'Aether'
ORG_NAME = os.environ.get('AETHER_ORG_NAME', 'eHealth Africa')

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
    'aether.ui',
]

TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'aether.ui.context_processors.aether',
]

MIGRATION_MODULES = {
    'ui': 'aether.ui.migrations'
}

# check the available modules linked to this instance
AETHER_MODULES = os.environ.get('AETHER_MODULES', '').split(',')

AETHER_KERNEL_TOKEN = os.environ.get('AETHER_KERNEL_TOKEN')
if TESTING:  # pragma: no cover
    AETHER_KERNEL_URL = os.environ.get('AETHER_KERNEL_URL_TEST')
else:  # pragma: no cover
    AETHER_KERNEL_URL = os.environ.get('AETHER_KERNEL_URL')

# check if ODK is available in this instance
AETHER_ODK = ('odk-importer' in AETHER_MODULES)
if AETHER_ODK:  # pragma: no cover
    AETHER_ODK_TOKEN = os.environ.get('AETHER_ODK_TOKEN')
    if TESTING:
        AETHER_ODK_URL = os.environ.get('AETHER_ODK_URL_TEST')
    else:
        AETHER_ODK_URL = os.environ.get('AETHER_ODK_URL')
