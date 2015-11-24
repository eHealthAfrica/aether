from importer.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'odkimporter',
        'USER': 'odkimportuser',
        'PASSWORD': 'importnow!',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}
