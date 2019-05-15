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

from bravado.requests_client import Authenticator, RequestsClient
import requests

from oauthlib.oauth2 import (
    TokenExpiredError,
    is_secure_transport,
    InsecureTransportError
)

from requests_oauthlib import (
    OAuth2Session,
    TokenUpdated
)
import os
import typing
from urllib.parse import urlparse

from .logger import LOG

# don't force https for oauth requests
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class OauthClient(RequestsClient):
    """Synchronous HTTP client implementation.
    """

    def __init__(self, authenticator, ssl_verify=True, ssl_cert=None):
        """
        :param ssl_verify: Set to False to disable SSL certificate validation.
            Provide the path to a CA bundle if you need to use a custom one.
        :param ssl_cert: Provide a client-side certificate to use. Either a
            sequence of strings pointing to the certificate (1) and the private
             key (2), or a string pointing to the combined certificate and key.
        """
        self.session = authenticator.session
        self.authenticator = authenticator
        self.ssl_verify = ssl_verify
        self.ssl_cert = ssl_cert

    def authenticated_request(self, request_params):
        # type: (typing.Mapping[str, typing.Any]) -> requests.Request
        return self.apply_authentication(
            self.session.request(execute=False, **request_params))


class OauthAuthenticator(Authenticator):

    def __init__(
        self,
        server,
        realm,
        user=None,
        pw=None,
        keycloak_url=None,
        offline_token=None
    ):
        self.realm = realm
        self.host = urlparse(server).netloc
        self.session = get_session(
            server, realm, user, pw, keycloak_url, offline_token)

    def bind_client(self, client):
        client.session = self.session
        client.authenticator = self

    def get_spec(self, spec_url):
        res = self.session.get(spec_url)
        spec = res.json()
        spec['host'] = f'{spec["host"]}/{self.realm}/kernel'
        sec_def = spec['securityDefinitions']
        sec_def['Authorization'] = {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
        spec['securityDefinitions'] = sec_def
        spec['security'] = [{'Authorization': []}]
        return spec

    def apply(self, req):
        # we don't need to do anything here
        return req


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


def get_session(
    server,
    realm,
    user=None,
    pw=None,
    keycloak_url=None,
    offline_token=None
):
    if not ((pw and user) or offline_token):
        raise ValueError('Either offline token, or user credentials for'
                         'password grant must be included.')
    if user:
        scope = 'profile openid email'
    else:
        scope = 'email offline_access profile'
    base_url = keycloak_url or f'{server}/keycloak/auth'
    token_url = f'{base_url}/realms/{realm}/protocol/openid-connect/token'
    LOG.debug(f'token url: {token_url}')
    initial_token = get_initial_token(user, pw, token_url, offline_token)
    LOG.debug(f'initial_token: {initial_token}')
    extras = {
        'client_id': 'aether',
    }
    return PreparableOauth2Session(
        user,
        token=initial_token,
        auto_refresh_url=token_url,
        auto_refresh_kwargs=extras,
        scope=scope,
        token_updater=_do_nothing  # on update, but is not the updater
    )


def _do_nothing(token):
    LOG.info('Updated access token')
    pass


def get_initial_token(user=None, pw=None, token_url=None, offline_token=None):
    grant = None
    if (user and pw):
        grant = 'password'
        data = {
            'client_id': 'aether',
            'username': user,
            'password': pw,
            'grant_type': grant,
            'scope': 'profile openid email'

        }
    elif offline_token:
        grant = 'refresh_token'
        data = {
            'client_id': 'aether',
            'refresh_token': offline_token,
            'grant_type': grant,
            'scope': 'profile openid email'

        }
    else:
        raise ValueError('Either pw grant or offline_token must be used')
    res = requests.post(token_url, data=data)
    LOG.info(f'Got refresh token via {grant}. Status:{res.status_code}')
    return res.json()
