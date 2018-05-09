"""
This settings are only used for testing purposes.
The app that includes this module should have its own settings.
"""

from aether.common.conf.settings import *  # noqa


ROOT_URLCONF = 'aether.common.urls'


# Database Configuration
# ------------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
