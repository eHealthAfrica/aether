# Common settings
# ------------------------------------------------------------------------------

from aether.common.conf.settings import *  # noqa
from aether.common.conf.settings import INSTALLED_APPS, REST_FRAMEWORK


# Kernel Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'aether.kernel.urls'
WSGI_APPLICATION = 'aether.kernel.wsgi.application'
ADD_REVERSION_ADMIN = True

INSTALLED_APPS += [
    'django_filters',
    'rest_framework_filters',
    'reversion',
    'reversion_compare',
    'aether.kernel',  # this enables signals
]

MIGRATION_MODULES = {
    'kernel': 'aether.kernel.api.migrations'
}
REST_FRAMEWORK['DEFAULT_VERSIONING_CLASS'] = 'rest_framework.versioning.NamespaceVersioning'
REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'] = (
    'rest_framework_filters.backends.DjangoFilterBackend',
    'rest_framework.filters.SearchFilter',
    'rest_framework.filters.OrderingFilter',
)
