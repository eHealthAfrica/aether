import os

# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS, TEMPLATES, STATIC_ROOT


# UI Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.ui.urls'
WSGI_APPLICATION = 'aether.ui.wsgi.application'

APP_NAME = 'aether'

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
    'aether.ui.context_processors.ui_context',
]

MIGRATION_MODULES = {
    'ui': 'aether.ui.api.migrations'
}
