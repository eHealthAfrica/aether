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

from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from .utils import check_user_token, check_gateway_token


class GatewayAuthenticationMiddleware(SessionMiddleware):

    def process_request(self, request):
        # SessionMiddleware sets the session object in the request
        # being accessible at `request.session`
        super(GatewayAuthenticationMiddleware, self).process_request(request)

        # checks the gateway keycloak token, if fails then forces logout
        check_gateway_token(request)


class TokenAuthenticationMiddleware(AuthenticationMiddleware):

    def process_request(self, request):
        # AuthenticationMiddleware sets the authenticated user in the request
        # being accessible at `request.user`
        super(TokenAuthenticationMiddleware, self).process_request(request)

        # checks the user keycloak token, if fails then forces logout
        check_user_token(request)
