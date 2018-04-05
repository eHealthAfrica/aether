import os

# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS, TESTING, STATIC_ROOT


# UI Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.ui.urls'
WSGI_APPLICATION = 'aether.ui.wsgi.application'

APP_NAME = 'Aether UI'

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

MIGRATION_MODULES = {
    'ui': 'aether.ui.api.migrations'
}

# Aether external modules
# ------------------------------------------------------------------------------

AETHER_APPS = {}

# check the available modules linked to this instance
AETHER_MODULES = [
    x
    for x in map(str.strip, os.environ.get('AETHER_MODULES', '').split(','))
    if x
]


# KERNEL is always a linked module
kernel = {
    'token': os.environ.get('AETHER_KERNEL_TOKEN', ''),
    'url': os.environ.get('AETHER_KERNEL_URL', ''),
}
if TESTING:  # pragma: no cover
    kernel['url'] = os.environ.get('AETHER_KERNEL_URL_TEST', '')

if kernel['url'].strip() and kernel['token'].strip():  # pragma: no cover
    AETHER_APPS['kernel'] = kernel
