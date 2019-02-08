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

from rest_framework.authentication import BaseAuthentication


class JwtTokenAuthentication(BaseAuthentication):
    '''
    Simple JWT token based authentication.

    Clients should authenticate by passing the token key and realm in the cookies.
    '''

    PK = {}

    def authenticate(self, request):

        if settings.REALM_COOKIE and settings.JWT_COOKIE in request.COOKIES:
            token = request.COOKIES[settings.JWT_COOKIE]
            realm = request.COOKIES[settings.REALM_COOKIE]

            if not realm:
                return None

            if realm not in self.PK:
                try:
                    self.PK[realm] = self.__get_public_key(realm)
                except Exception:
                    return None

            try:
                decoded = jwt.decode(token, self.PK[realm], audience='account', algorithms='RS256')
            except jwt.ExpiredSignatureError:
                return None

            # Create user
            try:
                username = decoded['preferred_username']
            except KeyError:
                return None

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
                return (user, None)

        return None

    def authenticate_header(self, request):
        realm = request.COOKIES.get(settings.REALM_COOKIE, 'default')
        return f'JWT realm="{realm}"'

    def __get_public_key(self, realm):
        ssl_header = settings.SECURE_PROXY_SSL_HEADER
        scheme = ssl_header[1] if ssl_header else 'http'
        url = f'{scheme}://{settings.KEYCLOAK_INTERNAL}/keycloak/auth/realms/{realm}/protocol/openid-connect/certs'

        res = requests.get(url)
        res.raise_for_status()

        jwk_key = res.json()['keys'][0]
        key_obj = JWK(**jwk_key)
        return str(key_obj.export_to_pem(), 'utf-8')
