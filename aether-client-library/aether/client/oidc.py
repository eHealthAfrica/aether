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

import os
import typing

from bravado.requests_client import Authenticator, RequestsClient
from oauthlib.oauth2 import (
    TokenExpiredError,
    is_secure_transport,
    InsecureTransportError,
)
import requests
from requests_oauthlib import (
    OAuth2Session,
    TokenUpdated,
)

from .logger import LOG
from .exceptions import AetherAPIException

# don't force https for oauth requests
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

KEYCLOAK_AETHER_CLIENT = os.environ.get('KEYCLOAK_AETHER_CLIENT', 'aether')
TOKEN_HEADER_KEY = os.environ.get('OAUTH_TOKEN_HEADER_KEY', 'X-CSRFToken')
TOKEN_COOKIE_KEY = os.environ.get('OAUTH_TOKEN_COOKIE_KEY', 'csrftoken')
TOKEN_URL = '{auth_url}/realms/{realm}/protocol/openid-connect/token'


class OauthAuthenticator(Authenticator):

    def __init__(
        self,
        host,
        keycloak_url,
        realm,
        username=None,
        password=None,
        offline_token=None,
        endpoint_name='kernel',
    ):
        self.host = host
        self.realm = realm
        self.endpoint_name = endpoint_name
        self.session = _get_session(
            TOKEN_URL.format(auth_url=keycloak_url, realm=realm),
            username, password, offline_token)

    def bind_client(self, client):
        client.session = self.session
        client.authenticator = self

    def get_spec(self, spec_url):
        res = self.session.get(spec_url)
        self.csrf = res.cookies.get(TOKEN_COOKIE_KEY)
        LOG.debug(f'Set CSRFToken: {self.csrf}')

        spec = res.json()
        spec['host'] = f'{spec["host"]}/{self.realm}/{self.endpoint_name}'
        sec_def = spec['securityDefinitions']
        sec_def['Authorization'] = {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
        spec['securityDefinitions'] = sec_def
        spec['security'] = [{'Authorization': []}]
        return spec

    def apply(self, request):
        # add CSRF Token
        request.headers[TOKEN_HEADER_KEY] = self.csrf
        return request


class PreparableOauth2Session(OAuth2Session):

    def request(
        self,
        method,
        url,
        data=None,
        headers=None,
        withhold_token=False,
        client_id=None,
        client_secret=None,
        execute=True,
        **kwargs
    ):
        """Intercept all requests and add the OAuth 2 token if present."""
        if not is_secure_transport(url):
            raise InsecureTransportError()
        if self.token and not withhold_token:
            LOG.debug(
                "Invoking %d protected resource request hooks.",
                len(self.compliance_hook["protected_request"]),
            )
            for hook in self.compliance_hook["protected_request"]:
                LOG.debug("Invoking hook %s.", hook)
                url, headers, data = hook(url, headers, data)

            LOG.debug("Adding token %s to request.", self.token)
            try:
                url, headers, data = self._client.add_token(
                    url, http_method=method, body=data, headers=headers
                )
            # Attempt to retrieve and save new access token if expired
            except TokenExpiredError:
                if self.auto_refresh_url:
                    LOG.debug(
                        "Auto refresh is set, attempting to refresh at %s.",
                        self.auto_refresh_url,
                    )

                    # We mustn't pass auth twice.
                    auth = kwargs.pop("auth", None)
                    if client_id and client_secret and (auth is None):
                        LOG.debug(
                            f'Encoding client_id "{client_id}" with'
                            ' client_secret as Basic auth credentials.'
                        )
                        auth = requests.auth.HTTPBasicAuth(
                            client_id, client_secret)
                    token = self.refresh_token(
                        self.auto_refresh_url, auth=auth, **kwargs
                    )
                    if self.token_updater:
                        LOG.debug(
                            f'Updating token to {token}'
                            f' using {self.token_updater}.'
                        )
                        self.token_updater(token)
                        url, headers, data = self._client.add_token(
                            url, http_method=method, body=data, headers=headers
                        )
                    else:
                        raise TokenUpdated(token)
                else:
                    raise
        LOG.debug("Requesting url %s using method %s.", url, method)
        LOG.debug("Supplying headers %s and data %s", headers, data)
        LOG.debug("Passing through key word arguments %s.", kwargs)
        if execute:
            return super(OAuth2Session, self).request(
                method, url, headers=headers, data=data, **kwargs
            )
        else:
            req = requests.models.Request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=data or {},
                **kwargs
            )
            return req


class OauthClient(RequestsClient):
    """Synchronous HTTP client implementation.
    """

    def set_oauth(
        self,
        host,
        keycloak_url,
        realm,
        username=None,
        password=None,
        offline_token=None,
        endpoint_name='kernel',
    ):
        self.authenticator = OauthAuthenticator(
            host, keycloak_url, realm, username, password,
            offline_token, endpoint_name,
        )

    def authenticated_request(self, request_params):
        # type: (typing.Mapping[str, typing.Any]) -> requests.Request
        return self.apply_authentication(
            self.session.request(execute=False, **request_params))


def _get_session(
    token_url,
    username=None,
    password=None,
    offline_token=None,
):
    if not ((password and username) or offline_token):
        raise ValueError('Either offline token, or username credentials for'
                         'password grant must be included.')
    LOG.debug(f'token url: {token_url}')

    initial_token = _get_initial_token(token_url, username, password, offline_token)
    LOG.debug(f'initial_token: {initial_token}')

    if username:
        scope = 'profile openid email'
    else:
        scope = 'email offline_access profile'
    return PreparableOauth2Session(
        username,
        token=initial_token,
        auto_refresh_url=token_url,
        auto_refresh_kwargs={'client_id': KEYCLOAK_AETHER_CLIENT},
        scope=scope,
        token_updater=_do_nothing  # on update, but is not the updater
    )


def _get_initial_token(
    token_url,
    username=None,
    password=None,
    offline_token=None,
):
    grant = None
    if username and password:
        grant = 'password'
        data = {
            'client_id': KEYCLOAK_AETHER_CLIENT,
            'username': username,
            'password': password,
            'grant_type': grant,
            'scope': 'profile openid email'

        }
    elif offline_token:
        grant = 'refresh_token'
        data = {
            'client_id': KEYCLOAK_AETHER_CLIENT,
            'refresh_token': offline_token,
            'grant_type': grant,
            'scope': 'profile openid email'
        }
    else:
        raise ValueError('Either password grant or offline_token must be used')

    res = requests.post(token_url, data=data)
    try:
        res.raise_for_status()
        LOG.info(f'Got refresh token via {grant}. Status: {res.status_code}')
        return res.json()
    except requests.exceptions.HTTPError:
        raise AetherAPIException('Could not get initial token for OIDC auth.')


def _do_nothing(*args, **kwargs):
    LOG.info('Updated access token')
    pass
