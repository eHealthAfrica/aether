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

from django.contrib.auth import get_user_model
from django.http.response import JsonResponse
from django_keycloak.middleware import KeycloakMiddleware
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed, NotAuthenticated

import logging

LOG = logging.getLogger('root')
# LOG.addHandler(logging.StreamHandler())

import base64
from jwcrypto.jwk import JWK
import jwt
# from jwt.contrib.algorithms.pycrypto import RSAAlgorithm
# jwt.register_algorithm('RS256', RSAAlgorithm(RSAAlgorithm.SHA256))
import json
import requests


KC_URL = 'http://keycloak:8080/auth/'  # internal
KEYCLOAK_EXTERNAL = 'http://localhost:8080/auth/'

kcj = {}
PK = {}

def get_public_key(kc_url, realm):
    CERT_URL = f'{kc_url}realms/{realm}/protocol/openid-connect/certs'
    res = requests.get(
        CERT_URL
    )
    jwk_key = res.json()['keys'][0]
    key_obj = JWK(**jwk_key)
    RSA_PUB_KEY = str(key_obj.export_to_pem(), 'utf-8')
    return RSA_PUB_KEY

class AetherKCMiddleware(KeycloakMiddleware):
    pass

    def process_view(self, request, view_func, view_args, view_kwargs):
        print(request.COOKIES)
        cookies = request.COOKIES
        if 'aether-realm' and 'aether-jwt' in cookies:
            realm = request.COOKIES['aether-realm']
            token = request.COOKIES['aether-jwt']
            if not realm in PK:
                try:
                    PK[realm] = get_public_key(KC_URL, realm)
                except Exception:
                    return 1
            decoded = jwt.decode(token, PK[realm], audience='account', algorithms='RS256')
            # Create user
            # add user to request as request.user?
            print(decoded)
            print(realm, token)
            #username = 
            # try:
            #   user = user_model.get(username=username)
            # except UserModel.DoesNotExist:
            #     user = user_model.create_user(
            #         username=username,
            #         password=user_model.make_random_password(length=100),
            #     )

        return None

        # """
        # Validate only the token introspect.
        # :param request: django request
        # :param view_func:
        # :param view_args: view args
        # :param view_kwargs: view kwargs
        # :return:
        # """


        # # try:
        # #     view_scopes = view_func.view_class.keycloak_scopes
        # # except AttributeError as e:
        # #     raise Exception("Scopes mappers not found.")
        # if 'HTTP_AUTHORIZATION' not in request.META:
        #     return None
        #     # return JsonResponse({"detail": NotAuthenticated.default_detail},
        #     #                     status=NotAuthenticated.status_code)

        # token = request.META.get('HTTP_AUTHORIZATION')

        # # # Get default if method is not defined.
        # # required_scope = view_scopes.get(request.method, None) \
        # #     if view_scopes.get(request.method, None) else view_scopes.get('DEFAULT', None)

        # # # DEFAULT scope not found and DEFAULT_ACCESS is DENY
        # # if not required_scope and self.default_access == 'DENY':
        # #     return JsonResponse({"detail": PermissionDenied.default_detail},
        # #                         status=PermissionDenied.status_code)
        
        # try:
        #     user_permissions = self.keycloak.get_permissions(token,
        #                                                      method_token_info=self.method_validate_token.lower(),
        #                                                      key=self.client_public_key)
        # except KeycloakInvalidTokenError as e:
        #     return None
        #     # return JsonResponse({"detail": AuthenticationFailed.default_detail},
        #     #                     status=AuthenticationFailed.status_code)

        # for perm in user_permissions:
        #     if required_scope in perm.scopes:
        #         return None

        # # User Permission Denied
        # return JsonResponse({"detail": PermissionDenied.default_detail},
        #                     status=PermissionDenied.status_code)