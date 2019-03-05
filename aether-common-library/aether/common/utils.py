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
