# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
import os


# Common Configuration
# ------------------------------------------------------------------------------

# Environment variables are false if unset or set to empty string, anything
# else is considered true.
DEBUG = bool(os.environ.get('DEBUG'))
TESTING = bool(os.environ.get('TESTING'))
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

APP_NAME = os.environ.get('APP_NAME', 'aether')
APP_ID = os.environ.get('APP_ID', 'aether-module-name')  # URL Friendly
APP_LINK = os.environ.get('APP_LINK', 'http://aether.ehealthafrica.org')

BASE_HOST = os.environ.get('BASE_HOST', 'aether.local')
KEYCLOAK_INTERNAL = os.environ.get('KEYCLOAK_INTERNAL', 'keycloak:8080')

REALM_COOKIE = os.environ.get('REALM_COOKIE', 'aether-realm')
JWT_COOKIE = os.environ.get('JWT_COOKIE', 'aether-jwt')

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = f'/{APP_ID}/static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/var/www/static/')

MEDIA_URL = '/media/'
MEDIA_BASIC_URL = '/media-basic/'
MEDIA_INTERNAL_URL = '/media-internal/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/media/')


# Version and revision
# ------------------------------------------------------------------------------

try:
    with open('/code/VERSION') as fp:
        VERSION = fp.read().strip()
except Exception:
    VERSION = '#.#.#'

try:
    with open('/code/REVISION') as fp:
        REVISION = fp.read().strip()
except Exception:
    REVISION = '---'


# Django Basic Configuration
# ------------------------------------------------------------------------------

INSTALLED_APPS = [
    # Basic Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.postgres',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'storages',

    # REST framework with auth token
    'rest_framework',
    'rest_framework.authtoken',

    # CORS checking
    'corsheaders',

    # Monitoring
    'django_prometheus',

    # aether apps
    'aether.common',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'aether.common.auth.middleware.JWTAuthentication'
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'aether.common.context_processors.aether_context',
            ],
        },
    },
]


# REST Framework Configuration
# ------------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'aether.common.drf.renderers.CustomBrowsableAPIRenderer',
        'aether.common.drf.renderers.CustomAdminRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'aether.common.drf.pagination.CustomPagination',
    'PAGE_SIZE': int(os.environ.get('PAGE_SIZE', 10)),
    'MAX_PAGE_SIZE': int(os.environ.get('MAX_PAGE_SIZE', 5000)),
    'HTML_SELECT_CUTOFF': int(os.environ.get('HTML_SELECT_CUTOFF', 100)),
}


# Database Configuration
# ------------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'PASSWORD': os.environ['PGPASSWORD'],
        'USER': os.environ['PGUSER'],
        'HOST': os.environ['PGHOST'],
        'PORT': os.environ['PGPORT'],
        'TESTING': {'CHARSET': 'UTF8'},
    },
}


# Logging Configuration
# ------------------------------------------------------------------------------

# https://docs.python.org/3.6/library/logging.html#levels
LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', logging.INFO)
LOGGING_CLASS = 'logging.StreamHandler' if not TESTING else 'logging.NullHandler'
LOGGING_FORMAT = '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
LOGGING_FORMATTER = os.environ.get('LOGGING_FORMATTER')
if LOGGING_FORMATTER != 'verbose':
    LOGGING_FORMATTER = 'json'

logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': LOGGING_LEVEL,
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': LOGGING_FORMAT,
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': LOGGING_FORMAT,
        },
    },
    'handlers': {
        'console': {
            'level': LOGGING_LEVEL,
            'class': LOGGING_CLASS,
            'formatter': LOGGING_FORMATTER,
        },
    },
    'loggers': {
        'aether': {
            'level': LOGGING_LEVEL,
            'handlers': ['console', ],
            'propagate': False,
        },
        'django': {
            'level': LOGGING_LEVEL,
            'handlers': ['console', ],
            'propagate': False,
        },
    },
}

# https://docs.sentry.io/platforms/python/django/
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), ]
    )

else:
    logger.info('No SENTRY enabled!')


# Authentication Configuration
# ------------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CAS_SERVER_URL = os.environ.get('CAS_SERVER_URL')
if CAS_SERVER_URL:
    INSTALLED_APPS += [
        # CAS libraries
        'django_cas_ng',
        'ums_client',
    ]
    AUTHENTICATION_BACKENDS += [
        'ums_client.backends.UMSRoleBackend',
    ]
    CAS_VERSION = 3
    CAS_LOGOUT_COMPLETELY = True
    HOSTNAME = os.environ['HOSTNAME']

else:
    logger.info('No CAS enabled!')

    LOGIN_TEMPLATE = os.environ.get('LOGIN_TEMPLATE', 'aether/login.html')
    LOGGED_OUT_TEMPLATE = os.environ.get('LOGGED_OUT_TEMPLATE', 'aether/logged_out.html')


# Security Configuration
# ------------------------------------------------------------------------------

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

CORS_ORIGIN_ALLOW_ALL = True

CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', '.aether.org')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', CSRF_COOKIE_DOMAIN).split(',')
SESSION_COOKIE_DOMAIN = CSRF_COOKIE_DOMAIN

if os.environ.get('DJANGO_USE_X_FORWARDED_HOST', True):
    USE_X_FORWARDED_HOST = True

if os.environ.get('DJANGO_USE_X_FORWARDED_PORT', False):
    USE_X_FORWARDED_PORT = True

if os.environ.get('DJANGO_HTTP_X_FORWARDED_PROTO', False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Storage Configuration
# ------------------------------------------------------------------------------

DJANGO_STORAGE_BACKEND = os.environ['DJANGO_STORAGE_BACKEND']

if DJANGO_STORAGE_BACKEND == 'filesystem':
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    HOSTNAME = os.environ['HOSTNAME']
    if not HOSTNAME:
        msg = 'Missing HOSTNAME environment variable!'
        logger.critical(msg)
        raise RuntimeError(msg)

elif DJANGO_STORAGE_BACKEND == 's3':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    try:
        AWS_STORAGE_BUCKET_NAME = os.environ['BUCKET_NAME']
        AWS_S3_REGION_NAME = os.environ['AWS_S3_REGION_NAME']
        AWS_DEFAULT_ACL = os.environ['AWS_DEFAULT_ACL']
    except KeyError as key:
        msg = f'Missing {key} environment variable!'
        logger.critical(msg)
        raise RuntimeError(msg)

elif DJANGO_STORAGE_BACKEND == 'gcs':
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = os.environ['BUCKET_NAME']
    if not GS_BUCKET_NAME:
        msg = 'Missing BUCKET_NAME environment variable!'
        logger.critical(msg)
        raise RuntimeError(msg)

else:
    msg = (
        'Unrecognized value "{}" for environment variable DJANGO_STORAGE_BACKEND.'
        ' Expected one of the following: "filesystem", "s3", "gcs"'
    )
    raise RuntimeError(msg.format(DJANGO_STORAGE_BACKEND))

logger.info('Using storage backend "{}"'.format(DJANGO_STORAGE_BACKEND))


# Debug Configuration
# ------------------------------------------------------------------------------

if not TESTING and DEBUG:
    INSTALLED_APPS += ['debug_toolbar', ]
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda _: True,
        'SHOW_TEMPLATE_CONTEXT': True,
    }


# Prometheus Configuration
# ------------------------------------------------------------------------------

MIDDLEWARE = [
    # Make sure this stays as the first middleware
    'django_prometheus.middleware.PrometheusBeforeMiddleware',

    *MIDDLEWARE,

    # Make sure this stays as the last middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]


# Local Configuration
# ------------------------------------------------------------------------------
# This scriptlet allows you to include custom settings in your local environment

try:
    from local_settings import *  # noqa
except ImportError:
    logger.debug('No local settings!')
