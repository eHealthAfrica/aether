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

from django.http import HttpResponse
from django.utils.translation import ugettext as _

from .utils import test_connection


BAD_RESPONSE = _('Always Look on the Bright Side of Life!!!')
OK_RESPONSE = _('Brought to you by eHealth Africa - good tech for hard places')


def check_kernel(*args, **kwargs):
    '''
    Check if the connection with Kernel server is possible
    '''

    if not test_connection():
        return HttpResponse(BAD_RESPONSE, status=500)
    return HttpResponse(OK_RESPONSE)
