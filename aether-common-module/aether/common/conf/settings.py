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


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if DEBUG:
    logger.setLevel(logging.DEBUG)
if TESTING:
    logger.setLevel(logging.CRITICAL)

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/var/www/static/')

MEDIA_URL = '/media/'
MEDIA_BASIC_URL = '/media-basic/'
MEDIA_INTERNAL_URL = '/media-internal/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/media/')


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
    'rest_framework_csv',

    # CORS checking
    'corsheaders',

    # Monitoring
    'django_prometheus',

    # aether apps
    'aether.common',
]

MIDDLEWARE = [
    # Make sure this stays as the 1st middleware
    'django_prometheus.middleware.PrometheusBeforeMiddleware',

    # All middlewares go here
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Make sure this stays as the last middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
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
            ],
        },
    },
]


# REST Framework Configuration
# ------------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.AdminRenderer',
        'aether.common.drf.renderers.CustomCSVRenderer',
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

CAS_VERSION = 3
CAS_LOGOUT_COMPLETELY = True
CAS_SERVER_URL = os.environ.get('CAS_SERVER_URL', '')
HOSTNAME = os.environ.get('HOSTNAME', '')

if CAS_SERVER_URL:
    INSTALLED_APPS += [
        # CAS libraries
        'django_cas_ng',
        'ums_client',
    ]
    AUTHENTICATION_BACKENDS += [
        'ums_client.backends.UMSRoleBackend',
    ]
else:
    logger.info('No CAS enable!')


# Sentry Configuration
# ------------------------------------------------------------------------------

SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    INSTALLED_APPS += ['raven.contrib.django.raven_compat', ]
    MIDDLEWARE = [
        'raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',
    ] + MIDDLEWARE

    SENTRY_CLIENT = 'raven.contrib.django.raven_compat.DjangoClient'
    SENTRY_CELERY_LOGLEVEL = logging.INFO
else:
    logger.info('No SENTRY enable!')


# Security Configuration
# ------------------------------------------------------------------------------

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

CORS_ORIGIN_ALLOW_ALL = True

CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', '.aether.org')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', CSRF_COOKIE_DOMAIN).split(',')
SESSION_COOKIE_DOMAIN = CSRF_COOKIE_DOMAIN

if os.environ.get('DJANGO_USE_X_FORWARDED_HOST', False):
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
elif DJANGO_STORAGE_BACKEND == 's3':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.environ['BUCKET_NAME']
elif DJANGO_STORAGE_BACKEND == 'gcs':
    DEFAULT_FILE_STORAGE = 'storages.backends.gs.GSBotoStorage'
    GS_BUCKET_NAME = os.environ['BUCKET_NAME']
else:
    msg = 'DJANGO_STORAGE_BACKEND "{}" is currently not supported'
    raise Exception(msg.format(DJANGO_STORAGE_BACKEND))
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


# Local Configuration
# ------------------------------------------------------------------------------
# This scriptlet allows you to include custom settings in your local environment

try:
    from local_settings import *  # noqa
except ImportError:
    logger.info('No local settings!')
