import logging
import os

logger = logging.getLogger(__name__)


SECRET_KEY = 'n)&_bvxfe$g)gfa4b-uy&aqt$vx!w7jw%fyi9mc8#onh2^$m=='

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', '.ehealthafrica.org')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', CSRF_COOKIE_DOMAIN).split(',')


CAS_SERVER_URL = os.environ.get('CAS_SERVER_URL', 'https://ums-dev.ehealthafrica.org')
HOSTNAME = os.environ.get('HOSTNAME', 'localhost')

CORS_ORIGIN_ALLOW_ALL = True


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = (os.environ.get('DEBUG', '').lower() == 'true')

ROOT_URLCONF = 'gather2.urls'
WSGI_APPLICATION = 'gather2.wsgi.application'


INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django_cas_ng',
    'django_extensions',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'reversion',
    'reversion_compare',
    'ums_client',
    'raven.contrib.django.raven_compat',

    # gather2 apps
    'core',  # this enables signals
]

ADD_REVERSION_ADMIN = True

MIDDLEWARE_CLASSES = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # this is default
    'ums_client.backends.UMSRoleBackend'
)

CAS_VERSION = 3
CAS_LOGOUT_COMPLETELY = True


REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.AdminRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.CursorPagination',
    'PAGE_SIZE': 30,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_filters.backends.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

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
        'NAME': os.environ.get('RDS_DB_NAME', 'gather2'),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'db'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
    }
}

BROKER_URL = 'django://'

# Sentry Configuration
# ------------------------------------------------------------------------------
# See https://docs.sentry.io/clients/python/integrations/django/

MIDDLEWARE_CLASSES = [
    'raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',
] + MIDDLEWARE_CLASSES

SENTRY_DSN = os.environ.get('SENTRY_DSN')
SENTRY_CLIENT = os.environ.get('DJANGO_SENTRY_CLIENT', 'raven.contrib.django.raven_compat.DjangoClient')
SENTRY_CELERY_LOGLEVEL = logging.INFO


if os.environ.get('DJANGO_USE_X_FORWARDED_HOST', False):
    USE_X_FORWARDED_HOST = True

if os.environ.get('DJANGO_USE_X_FORWARDED_PORT', False):
    USE_X_FORWARDED_PORT = True

if os.environ.get('DJANGO_HTTP_X_FORWARDED_PROTO', False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# This scriptlet allows you to include custom settings in your local environment
try:
    from local_settings import *  # noqa
except ImportError as e:
    logger.info('No local settings!')
