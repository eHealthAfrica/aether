# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS, REST_FRAMEWORK


# Core Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.core.urls'
WSGI_APPLICATION = 'aether.core.wsgi.application'
ADD_REVERSION_ADMIN = True

INSTALLED_APPS += [
    'django_filters',
    'rest_framework_filters',
    'reversion',
    'reversion_compare',
    'aether.core',  # this enables signals
]

MIGRATION_MODULES = {
    'core': 'aether.core.api.migrations'
}
REST_FRAMEWORK['DEFAULT_VERSIONING_CLASS'] = 'rest_framework.versioning.NamespaceVersioning'
REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'] = (
    'rest_framework_filters.backends.DjangoFilterBackend',
    'rest_framework.filters.SearchFilter',
    'rest_framework.filters.OrderingFilter',
)
