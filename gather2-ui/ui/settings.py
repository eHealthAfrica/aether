import logging
import os


# Core Configuration
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'ui.urls'
WSGI_APPLICATION = 'ui.wsgi.application'

APP_NAME = 'Gather'


# Common Configuration
# ------------------------------------------------------------------------------

DEBUG = (os.environ.get('DEBUG', '').lower() == 'true')
TESTING = (os.environ.get('TESTING', '').lower() == 'true')
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if DEBUG:  # pragma: no cover
    logger.setLevel(logging.DEBUG)
if TESTING:  # pragma: no cover
    logger.setLevel(logging.CRITICAL)


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/var/www/static/')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/tmp/')

# Javascript/CSS Files:
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': '/',  # used in prod
        'STATS_FILE': os.path.join(STATIC_ROOT, 'webpack-stats.json'),
    },
}


INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django_cas_ng',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'ums_client',
    'webpack_loader',

    # gather2 apps
    'ui',
]


MIDDLEWARE = [
    'raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'ui/templates/'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ui.context_processors.gather2'
            ],
        },
    },
]


# Database Configuration
# ------------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('RDS_DB_NAME', 'ui'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'db'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'TESTING': {'CHARSET': 'UTF8'},
    }
}


# REST Framework Configuration
# ------------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.CursorPagination',
    'PAGE_SIZE': 30,
}


# Authentication Configuration
# ------------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'ums_client.backends.UMSRoleBackend',
)

CAS_VERSION = 3
CAS_LOGOUT_COMPLETELY = True
CAS_SERVER_URL = os.environ.get('CAS_SERVER_URL', '')
HOSTNAME = os.environ.get('HOSTNAME', '')


# Sentry Configuration
# ------------------------------------------------------------------------------

SENTRY_DSN = os.environ.get('SENTRY_DSN')
SENTRY_CLIENT = os.environ.get(
    'DJANGO_SENTRY_CLIENT',
    'raven.contrib.django.raven_compat.DjangoClient'
)
SENTRY_CELERY_LOGLEVEL = logging.INFO


# Security Configuration
# ------------------------------------------------------------------------------

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

CORS_ORIGIN_ALLOW_ALL = True

CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', '.gather2.org')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', CSRF_COOKIE_DOMAIN).split(',')
SESSION_COOKIE_DOMAIN = CSRF_COOKIE_DOMAIN

if os.environ.get('DJANGO_USE_X_FORWARDED_HOST', False):  # pragma: no cover
    USE_X_FORWARDED_HOST = True

if os.environ.get('DJANGO_USE_X_FORWARDED_PORT', False):  # pragma: no cover
    USE_X_FORWARDED_PORT = True

if os.environ.get('DJANGO_HTTP_X_FORWARDED_PROTO', False):  # pragma: no cover
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Debug Configuration
# ------------------------------------------------------------------------------

if DEBUG:  # pragma: no cover
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
except ImportError as e:
    logger.info('No local settings!')
