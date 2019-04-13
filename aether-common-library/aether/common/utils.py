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

import json
import requests

from time import sleep

from django.conf import settings
from django.utils.safestring import mark_safe

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer


def __prettified__(response, lexer):
    # Truncate the data. Alter as needed
    response = response[:settings.PRETTIFIED_CUTOFF]
    # Get the Pygments formatter
    formatter = HtmlFormatter(style='colorful')
    # Highlight the data
    response = highlight(response, lexer, formatter)
    # Get the stylesheet
    style = '<style>' + formatter.get_style_defs() + '</style>'
    # Safe the output
    return mark_safe(style + response)


def json_prettified(value, indent=2):
    '''
    Function to display pretty version of our json data
    https://www.pydanny.com/pretty-formatting-json-django-admin.html
    '''
    return __prettified__(json.dumps(value, indent=indent), JsonLexer())


def find_in_request(request, key, default_value=None):
    '''
    Finds the key in
        - the request session or
        - within the request cookies or
        - within the request headers.

    https://docs.djangoproject.com/en/2.2/ref/request-response/#django.http.HttpRequest.COOKIES
    https://docs.djangoproject.com/en/2.2/ref/request-response/#django.http.HttpRequest.META

    New in Django.2.2
    https://docs.djangoproject.com/en/2.2/ref/request-response/#django.http.HttpRequest.headers
    '''

    return getattr(request, 'session', {}).get(
        key,
        getattr(request, 'COOKIES', {}).get(
            key,
            getattr(request, 'headers', {}).get(  # New in Django.2.2
                key,
                getattr(request, 'META', {}).get(
                    'HTTP_' + key.replace('-', '_').upper(),  # HTTP_<KEY>,
                    default_value
                )
            )
        )
    )


def request(*args, **kwargs):
    '''
    Executes the request call at least three times to avoid
    unexpected connection errors (not request expected ones).

    Like:

        # ConnectionResetError: [Errno 104] Connection reset by peer
        # http.client.RemoteDisconnected: Remote end closed connection without response
    '''
    count = 0
    exception = None

    while count < 3:
        try:
            return requests.request(*args, **kwargs)
        except Exception as e:
            exception = e
        count += 1
        sleep(1)

    raise exception


def get_all_docs(url, **kwargs):
    '''
    Returns all documents linked to an url, even with pagination
    '''

    def _get_data(url):
        resp = request(method='get', url=url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    data = {'next': url}
    while data.get('next'):
        data = _get_data(data['next'])
        for x in data['results']:
            yield x
