import logging
import os

logger = logging.getLogger(__name__)


# SECURITY WARNING: this should also be considered a secret:
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

SECRET_KEY = '$%7as98^%*OgJYabsiyAyqfif65*_d43!c)3-7-$9f3ii%2z#^dox!rjhg6uw_a2$_3(wv'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', '.ehealthafrica.org')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', CSRF_COOKIE_DOMAIN).split(',')

# Allow cors for all origins but only for the sync endpoint
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r'^/sync/.*$'

CAS_SERVER_URL = os.environ.get('CAS_SERVER_URL', 'https://ums-dev.ehealthafrica.org')
HOSTNAME = os.environ.get('HOSTNAME', 'localhost')


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = (os.environ.get('DEBUG', '').lower() == 'true')

ROOT_URLCONF = 'sync.urls'
WSGI_APPLICATION = 'sync.wsgi.application'


INSTALLED_APPS = (
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django_cas_ng',
    'django_extensions',
    'django_rq',
    'rest_framework',
    'ums_client',

    # gather2 apps
    'api',
    'importer',
)

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

FIXTURE_DIRS = (
    'fixtures/',
)


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/var/www/static/')


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('RDS_DB_NAME', 'couchdb_sync'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'db'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
    }
}

COUCHDB_URL = os.environ.get('COUCHDB_URL', 'http://couchdb:5984')
COUCHDB_USER = os.environ.get('COUCHDB_USER', None)
COUCHDB_PASSWORD = os.environ.get('COUCHDB_PASSWORD', None)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    )
}


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # this is default
    'ums_client.backends.UMSRoleBackend'
)

CAS_VERSION = 3
CAS_LOGOUT_COMPLETELY = True

if os.environ.get('DJANGO_USE_X_FORWARDED_HOST', False):
    USE_X_FORWARDED_HOST = True

if os.environ.get('DJANGO_USE_X_FORWARDED_PORT', False):
    USE_X_FORWARDED_PORT = True

if os.environ.get('DJANGO_HTTP_X_FORWARDED_PROTO', False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Import processing
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 0)
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)


# RQ
RQ_QUEUES = {
    'default': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': REDIS_DB,
        'PASSWORD': REDIS_PASSWORD,
        'DEFAULT_TIMEOUT': 360,
    },
}
RQ_SHOW_ADMIN_LINK = True


# Check possible connection with CORE
def test_gather_core_connection():
    import requests

    fail_action = 'syncing data to core will not work'

    if GATHER_CORE_URL and GATHER_CORE_TOKEN:
        try:
            # check that the server is up
            h = requests.head(GATHER_CORE_URL)
            assert h.status_code == 200
            logger.info('GATHER_CORE_URL ({}) is up and responding!'.format(GATHER_CORE_URL))
            try:
                # check that the token is valid
                auth_token = {'Authorization': 'Token {}'.format(GATHER_CORE_TOKEN)}
                g = requests.get(GATHER_CORE_URL + '/surveys.json', headers=auth_token)
                assert g.status_code == 200, g.content
                logger.info('GATHER_CORE_TOKEN is valid!')

                return  # it's possible to connect with core

            except Exception as eg:
                logger.exception(
                    'GATHER_CORE_TOKEN is not valid for GATHER_CORE_URL ({}), {}'.format(
                        GATHER_CORE_URL, fail_action))
        except Exception as eh:
            logger.warning('GATHER_CORE_URL ({}) is not available, {}.'.format(
                GATHER_CORE_URL, fail_action))
    else:
        logger.warning(
            'GATHER_CORE_URL and/or GATHER_CORE_TOKEN are not set, {}.'.format(fail_action))

    # it's not possible to connect with core
    raise RuntimeError('Cannot connect to {}'.format(GATHER_CORE_URL))


GATHER_CORE_URL = os.environ.get('GATHER_CORE_URL')
GATHER_CORE_TOKEN = os.environ.get('GATHER_CORE_TOKEN')
try:
    test_gather_core_connection()
except RuntimeError as re:
    logger.warning('Cannot connect to {}'.format(GATHER_CORE_URL))


# This scriptlet allows you to include custom settings in your local environment
try:
    from local_settings import *  # noqa
except ImportError as e:
    logger.info('No local settings!')
