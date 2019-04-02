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

import urllib.parse

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.urls import reverse

from ..auth.utils import get_or_create_user
from ..utils import request as exec_request

_KC_TOKEN_SESSION = '__keycloak__token__session__'
_KC_URL = settings.KEYCLOAK_SERVER_URL
_KC_OID_URL = 'protocol/openid-connect'


def get_realm_auth_url(request):
    realm = request.session.get(settings.REALM_COOKIE)
    redirect_uri = urllib.parse.quote(_get_login_url(request), safe='')

    return (
        f'{_KC_URL}/{realm}/{_KC_OID_URL}/auth?'
        f'&client_id={settings.KEYCLOAK_CLIENT_ID}'
        '&scope=openid'
        '&response_type=code'
        f'&redirect_uri={redirect_uri}'
    )


def check_realm(realm):
    '''
    Checks if the realm name is valid visiting its keycloak server login page.
    '''

    response = exec_request(method='head', url=f'{_KC_URL}/{realm}/account')
    response.raise_for_status()


def authenticate(request, username, password, realm):
    '''
    Logs in in the keycloak server with the given username, password and realm.
    '''

    try:
        # get user token+info
        token, userinfo = _authenticate(
            realm=realm,
            data={
                'grant_type': 'password',
                'client_id': settings.KEYCLOAK_CLIENT_ID,
                'username': username,
                'password': password,
            })
    except Exception:
        return None

    # save the current realm in the session
    request.session[settings.REALM_COOKIE] = realm
    # save the user token in the session
    request.session[_KC_TOKEN_SESSION] = token

    return _get_or_create_user(request, userinfo)


def post_authenticate(request):
    session_state = request.GET.get('session_state')
    code = request.GET.get('code')
    realm = request.session.get(settings.REALM_COOKIE)

    if not session_state or not code or not realm:
        return

    redirect_uri = _get_login_url(request)
    token, userinfo = _authenticate(
        realm=realm,
        data={
            'grant_type': 'authorization_code',
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'client_session_state': session_state,
            'client_session_host': redirect_uri,
            'code': code,
            'redirect_uri': redirect_uri,
        })

    # save the user token in the session
    request.session[_KC_TOKEN_SESSION] = token

    return _get_or_create_user(request, userinfo)


def check_user_token(request):
    '''
    Checks if the user token is valid refreshing it in keycloak server.
    '''

    token = request.session.get(_KC_TOKEN_SESSION)
    realm = request.session.get(settings.REALM_COOKIE)
    if token:
        # refresh token
        response = exec_request(
            method='post',
            url=f'{_KC_URL}/{realm}/{_KC_OID_URL}/token',
            data={
                'grant_type': 'refresh_token',
                'client_id': settings.KEYCLOAK_CLIENT_ID,
                'refresh_token': token['refresh_token'],
            },
        )

        try:
            response.raise_for_status()
            request.session[_KC_TOKEN_SESSION] = response.json()
        except Exception:
            logout(request)


@receiver(user_logged_out)
def _user_logged_out(sender, user, request, **kwargs):
    '''
    Removes realm and token from session also logs out from keycloak server
    making the user token invalid.
    '''

    token = request.session.get(_KC_TOKEN_SESSION)
    realm = request.session.get(settings.REALM_COOKIE)

    if token:
        # logout
        exec_request(
            method='post',
            url=f'{_KC_URL}/{realm}/{_KC_OID_URL}/logout',
            data={
                'client_id': settings.KEYCLOAK_CLIENT_ID,
                'refresh_token': token['refresh_token'],
            },
        )

    # remove session values
    request.session[settings.REALM_COOKIE] = None
    request.session[_KC_TOKEN_SESSION] = None


def _get_login_url(request):
    return request.build_absolute_uri(reverse('rest_framework:login'))


def _authenticate(realm, data):
    # get user token from the returned "code"
    response = exec_request(
        method='post',
        url=f'{_KC_URL}/{realm}/{_KC_OID_URL}/token',
        data=data,
    )
    response.raise_for_status()

    token = response.json()
    userinfo = _get_user_info(realm, token)
    return token, userinfo


def _get_user_info(realm, token):
    response = exec_request(
        method='get',
        url=f'{_KC_URL}/{realm}/{_KC_OID_URL}/userinfo',
        headers={'Authorization': 'Bearer {}'.format(token['access_token'])},
    )
    response.raise_for_status()

    return response.json()


def _get_or_create_user(request, userinfo):
    user = get_or_create_user(request, userinfo.get('preferred_username'))

    user.first_name = userinfo.get('given_name') or ''
    user.last_name = userinfo.get('family_name') or ''
    user.email = userinfo.get('email') or ''
    user.save()

    return user
