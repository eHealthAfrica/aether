"""
WSGI config for gather2_odk_importer project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "importer.docker")

_application = get_wsgi_application()


def application(environ, start_response):
    # Check for custom header from load balancer, and use it
    # to manually set the url_scheme variable
    environ['wsgi.url_scheme'] = environ.get('HTTP_X_FORWARDED_PROTO', 'http')
    if environ['wsgi.url_scheme'] == 'https':
        environ['HTTPS'] = 'on'
    return _application(environ, start_response)
