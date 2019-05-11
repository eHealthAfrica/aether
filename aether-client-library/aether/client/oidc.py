# import bravado
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
import json
import os
import typing
from urllib.parse import urlparse

from .logger import LOG

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class NullAuth(requests.auth.AuthBase):
    def __init__(self, headers):
        self.headers = headers

    def __call__(self, r):
        for k, v in r.__dict__.items():
            print(k, v)
        return r


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
                            'Encoding client_id "%s" with client_secret as Basic auth credentials.',
                            client_id,
                        )
                        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
                    token = self.refresh_token(
                        self.auto_refresh_url, auth=auth, **kwargs
                    )
                    if self.token_updater:
                        LOG.debug(
                            "Updating token to %s using %s.", token, self.token_updater
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


def get_session(user, pw, server, realm, keycloak_url):
    base_url = keycloak_url or f'{server}/keycloak/auth'
    token_url = f'{base_url}/realms/{realm}/protocol/openid-connect/token'
    LOG.debug(f'token url: {token_url}')
    initial_token = get_initial_token(user, pw, token_url)
    LOG.debug(f'initial_token: {initial_token}')
    extras = {
        'client_id': 'aether',
    }
    return PreparableOauth2Session(
        user,
        token=initial_token,
        auto_refresh_url=token_url,
        auto_refresh_kwargs=extras,
        scope='profile openid email',
        token_updater=_do_nothing  # on update, but is not the updater
    )


def _do_nothing(token):
    LOG.debug('Updated token')
    pass


def get_initial_token(user, pw, token_url):
    data = {
        'client_id': 'aether',
        'username': user,
        'password': pw,
        'grant_type': 'password',
        'scope': 'profile openid email'

    }
    res = requests.post(token_url, data=data)
    LOG.debug(f'initial_token res: {res.text}')
    return res.json()


class OauthClient(RequestsClient): # bravado.http_client.HttpClient):
    """Synchronous HTTP client implementation.
    """

    def __init__(self, authenticator, ssl_verify=True, ssl_cert=None):
        """
        :param ssl_verify: Set to False to disable SSL certificate validation. Provide the path to a
            CA bundle if you need to use a custom one.
        :param ssl_cert: Provide a client-side certificate to use. Either a sequence of strings pointing
            to the certificate (1) and the private key (2), or a string pointing to the combined certificate
            and key.
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
        self, user, pw, server, realm, keycloak_url
    ):
        self.realm = realm
        self.host = urlparse(server).netloc
        self.session = get_session(user, pw, server, realm, keycloak_url)

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
        # import json
        # print(json.dumps(spec, indent=2))
        return spec

    def apply(self, req):
        # we don't need to do anything here
        LOG.error('REDECORATING!')
        req.auth = NullAuth(req.headers)
        LOG.debug(req.__dict__)
        # return self._session.request(**req.__dict__)
        return req
