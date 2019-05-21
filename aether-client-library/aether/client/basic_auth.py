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

from bravado.requests_client import Authenticator, RequestsClient
from requests.auth import HTTPBasicAuth
import requests
from urllib.parse import urlparse


class BasicRealmClient(RequestsClient):
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
        self.session = requests.Session()
        self.authenticator = authenticator
        self.ssl_verify = ssl_verify
        self.ssl_cert = ssl_cert

    def apply_authentication(self, request):
        return self.authenticator.apply(request)


class BasicRealmAuthenticator(Authenticator):

    def __init__(
        self,
        server,
        realm,
        user=None,
        pw=None
    ):
        self.realm = realm
        self.auth = HTTPBasicAuth(user, pw)
        self.host = urlparse(server).netloc

    def apply(self, req):
        req.auth = self.auth
        req.headers['aether-realm'] = self.realm
        return req
