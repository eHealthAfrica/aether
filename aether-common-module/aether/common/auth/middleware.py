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
import requests

from jwcrypto.jwk import JWK

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http.response import JsonResponse
from django.shortcuts import redirect as redirect_response
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext as _

from rest_framework.exceptions import AuthenticationFailed


class JWTAuthentication(MiddlewareMixin):
    # Cached Public Keys for validating JWTs of different realms
    PK = {}

    def process_request(self, request):
        if settings.REALM_COOKIE and settings.JWT_COOKIE in request.COOKIES:
            token = request.COOKIES[settings.JWT_COOKIE]
            realm = request.COOKIES[settings.REALM_COOKIE]

            if not realm:
                return JsonResponse(
                    {'detail': _('No realm included in request')},
                    status=AuthenticationFailed.status_code,
                )

            if realm not in self.PK:
                try:
                    self.PK[realm] = self.__get_public_key(realm)
                except Exception:
                    return self.__login_redirect(request, realm)

            try:
                decoded = jwt.decode(token, self.PK[realm], audience='account', algorithms='RS256')
            except jwt.ExpiredSignatureError:
                return self.__login_redirect(request, realm)

            # Create user
            try:
                username = decoded['preferred_username']
            except KeyError:
                return JsonResponse(
                    {'detail': AuthenticationFailed.default_detail},
                    status=AuthenticationFailed.status_code,
                )

            UserModel = get_user_model()
            user_model = UserModel.objects
            try:
                user = user_model.get(username=username)
            except UserModel.DoesNotExist:
                user = user_model.create_user(
                    username=username,
                    password=user_model.make_random_password(length=100),
                )
            finally:
                # add user to request as request.user
                request.user = user

        return None

    def __login_redirect(self, request, realm):
        scheme = self.__get_scheme()

        # We want to handle this with a redirect to the login screen.
        path = request.get_full_path()
        host = request.META['HTTP_X_FORWARDED_HOST']

        # on Success, the login page will redirect back to this original request
        redirect = f'{scheme}://{host}{path}'
        url = f'{scheme}://{settings.BASE_HOST}/auth/user/{realm}/refresh?redirect={redirect}'

        return redirect_response(url)

    def __get_public_key(self, realm):
        scheme = self.__get_scheme()
        url = f'{scheme}://{settings.KEYCLOAK_INTERNAL}/keycloak/auth/realms/{realm}/protocol/openid-connect/certs'

        res = requests.get(url)
        res.raise_for_status()

        jwk_key = res.json()['keys'][0]
        key_obj = JWK(**jwk_key)
        return str(key_obj.export_to_pem(), 'utf-8')

    def __get_scheme(self):
        ssl_header = settings.SECURE_PROXY_SSL_HEADER
        return ssl_header[1] if ssl_header else 'http'
