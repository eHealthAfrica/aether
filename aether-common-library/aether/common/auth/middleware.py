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

import jwt

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.sessions.middleware import SessionMiddleware

from aether.common.utils import find_in_request_headers
from .utils import get_or_create_user_from_userinfo


class GatewayAuthenticationMiddleware(SessionMiddleware):  # pragma: no cover

    def _logout(self, request):
        request.session[settings.REALM_COOKIE] = None
        request.session[settings.GATEWAY_HEADER_TOKEN] = None
        logout(request)

    def process_request(self, request):
        # SessionMiddleware sets the session object in the request
        # being accessible at `request.session`
        super(GatewayAuthenticationMiddleware, self).process_request(request)

        token = find_in_request_headers(request, settings.GATEWAY_HEADER_TOKEN)
        if token:
            try:
                userinfo = jwt.decode(token, verify=False)
                iss_url = userinfo['iss']

                # the only security check we are implementing so far... more coming
                if not iss_url.startswith(settings.GATEWAY_HOST):
                    return

                # get realm info from "iss"
                realm = iss_url.split('/')[-1]
                request.session[settings.REALM_COOKIE] = realm

                user = get_or_create_user_from_userinfo(userinfo)
                login(request, user)

                # flags that we are using the gateway to authenticate
                request.session[settings.GATEWAY_HEADER_TOKEN] = realm

            except Exception:
                # something went wrong
                self._logout(request)

        elif request.session.get(settings.GATEWAY_HEADER_TOKEN):
            # this session was using the gateway to authenticate before
            self._logout(request)
