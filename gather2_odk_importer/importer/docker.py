from importer.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'odkimporter',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'db',
        'PORT': '5432',
    }
}
