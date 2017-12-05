'''
This settings are only used for testing purposes.
The app that includes this module should have its own settings.
'''

import os

TESTING = True
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
ROOT_URLCONF = 'aether.common.urls'

# Django Applications
# ------------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_csv',
    'aether.common',
]

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
)


# Database Configuration
# ------------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}


# Authentication Configuration
# ------------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)


# REST Framework Configuration
# ------------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
}
