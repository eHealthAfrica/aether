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

import os

from django.conf import settings
from django.http import HttpResponse

from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated


# Taken from: http://glitterbug.in/blog/serving-protected-files-from-nginx-with-django-11/show/
def media_serve(request, path, *args, **kwargs):  # pragma: no cover
    '''
    Redirect the request to the path used by nginx for protected media.
    '''

    response = HttpResponse(status=200, content_type='')
    response['X-Accel-Redirect'] = os.path.join(settings.MEDIA_INTERNAL_URL, path)
    return response


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def basic_serve(request, path, *args, **kwargs):  # pragma: no cover
    '''
    Redirect the request to the path used by nginx for protected media using BASIC Authentication.
    '''

    return media_serve(request, path, *args, **kwargs)
