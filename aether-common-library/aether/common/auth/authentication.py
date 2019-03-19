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

from jwt import decode, ExpiredSignatureError
from jwcrypto.jwk import JWK

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.authentication import BaseAuthentication

from ..utils import request


def get_current_realm(request):
    return request.COOKIES.get(settings.REALM_COOKIE, settings.DEFAULT_REALM)


class JwtTokenAuthentication(BaseAuthentication):
    '''
    Simple JWT token based authentication.

    Clients should authenticate by passing the token key and realm in the cookies.
    '''

    PUBLIC_KEYS = {}

    def authenticate(self, request):
        UserModel = get_user_model()
        user_model = UserModel.objects

        try:
            realm = get_current_realm(request)
            token = request.COOKIES[settings.JWT_COOKIE]

            if realm not in self.PUBLIC_KEYS:
                self.PUBLIC_KEYS[realm] = self.__get_public_key(realm)

            decoded = decode(token, self.PUBLIC_KEYS[realm], audience='account', algorithms='RS256')
            username = decoded['preferred_username']

            # Create user
            try:
                user = user_model.get(username=username)
            except UserModel.DoesNotExist:
                user = user_model.create_user(
                    username=username,
                    password=user_model.make_random_password(length=100),
                )
            finally:
                return (user, None)

        except (ExpiredSignatureError, KeyError, Exception):
            return None

        return None

    def authenticate_header(self, request):
        realm = get_current_realm(request)
        return f'JWT realm="{realm}"'

    def __get_public_key(self, realm):
        url = f'{settings.KEYCLOAK_URL}/keycloak/auth/realms/{realm}/protocol/openid-connect/certs'

        res = requests(method='get', url=url)
        res.raise_for_status()

        jwk_key = res.json()['keys'][0]
        key_obj = JWK(**jwk_key)
        return str(key_obj.export_to_pem(), 'utf-8')
