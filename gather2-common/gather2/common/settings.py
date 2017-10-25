'''
This settings are only used for testing purposes.
The app that includes this module should have its own settings.
'''

import os

TESTING = True
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
ROOT_URLCONF = 'gather2.common.urls'

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
    'gather2.common',
]

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
)


# Database Configuration
# ------------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('RDS_DB_NAME', 'common'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'db'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'TESTING': {'CHARSET': 'UTF8'},
    }
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
