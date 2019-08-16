# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.utils.translation import gettext_lazy as _

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from aether.sdk.auth.authentication import BasicAuthentication
from aether.sdk.multitenancy.utils import check_user_in_realm

from .auth_utils import check_authorization_header, get_www_authenticate_header


class CollectAuthentication(BaseAuthentication):
    '''
    Use Basic or Digest authentication depending on the autorization header.
    '''

    def authenticate(self, request):
        try:
            auth = get_authorization_header(request).split()
            method = auth[0].lower()
            if method not in (b'basic', b'digest'):
                return None
        except Exception:
            return None

        if method == b'basic':
            # SECURITY CHECK: this runs over "https" and not "http"
            host = request.build_absolute_uri(request.path)
            if not host.startswith('https://'):
                msg = _('Basic authentication is only allowed over HTTPS')
                raise AuthenticationFailed(msg)

            return BasicAuthentication().authenticate(request)

        # HTTP Digest authentication
        if len(auth) == 1:
            msg = _('Invalid digest header. No credentials provided.')
            raise AuthenticationFailed(msg)

        user = check_authorization_header(request)

        if not user.is_active:
            raise AuthenticationFailed(_('User inactive or deleted.'))

        # check that the user belongs to the current realm
        if not check_user_in_realm(request, user):
            raise AuthenticationFailed(_('Invalid user in this realm.'))

        return (user, None)

    def authenticate_header(self, request):
        '''
        Return the Digest header (default authentication class)
        '''
        return get_www_authenticate_header(request)
