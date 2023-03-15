# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import base64
import hashlib
import os
import sys
import time

from importlib import reload, import_module

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.timezone import now

from aether.sdk.unittest import UrlsTestCase

from ...serializers import SurveyorSerializer

from ..auth_utils import (
    COLLECT_REALM,
    COLLECT_NONCE_LIFESPAN,
    parse_authorization_header,
)


def md5_utf8(x):
    if isinstance(x, str):
        x = x.encode('utf-8')
    return hashlib.md5(x).hexdigest()


def KD(s, d):
    return md5_utf8(f'{s}:{d}')


def build_digest_header(
        username,
        password,
        challenge_header,
        method,
        path,
        nonce=None,
        nonce_count=1,
        cnonce=None,
        algorithm='MD5',
        qop='auth',
):
    challenge_data = parse_authorization_header(challenge_header)
    realm = challenge_data['realm']
    nonce = nonce or challenge_data['nonce']
    qop = challenge_data['qop']
    opaque = challenge_data['opaque']

    A1 = f'{username}:{realm}:{password}'
    A2 = f'{method}:{path}'

    ncvalue = '%08x' % nonce_count

    if cnonce is None:
        seed = str(nonce_count).encode('utf-8')
        seed += nonce.encode('utf-8')
        seed += time.ctime().encode('utf-8')
        seed += os.urandom(8)
        cnonce = (hashlib.sha1(seed).hexdigest()[:16])

    noncebit = '%s:%s:%s:%s:%s' % (nonce, ncvalue, cnonce, qop, md5_utf8(A2))
    respdig = KD(md5_utf8(A1), noncebit)

    base = 'username="%s", realm="%s", nonce="%s", uri="%s", ' \
           'response="%s", algorithm="%s"'
    base = base % (username, realm, nonce, path, respdig, algorithm)

    if opaque:
        base += ', opaque="%s"' % opaque
    if qop:
        base += ', qop=%s, nc=%s, cnonce="%s"' % (qop, ncvalue, cnonce)
    return 'Digest %s' % base


@override_settings(MULTITENANCY=False)
class AuthenticationTests(UrlsTestCase):

    def setUp(self):
        super(AuthenticationTests, self).setUp()

        self.username = 'surveyor'
        self.password = '~t]:vS3Q>e{2k]CE'
        self.url = reverse('xform-list-xml')

        # The surveyor must be created using the serializer
        user = SurveyorSerializer(
            data={
                'username': self.username,
                'password': self.password,
            },
            context={'request': RequestFactory().get(self.url)},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()
        self.user = get_user_model().objects.get(pk=user.data['id'])

    def test_challenge(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertIn('WWW-Authenticate', response)
        challenge = response['WWW-Authenticate']
        self.assertIn('Digest ', challenge)
        self.assertIn(f' realm="{COLLECT_REALM}"', challenge)
        self.assertIn(' qop="auth', challenge)
        self.assertIn(' algorithm="MD5"', challenge)
        self.assertIn(' stale="false"', challenge)
        self.assertIn(' opaque="', challenge)
        self.assertIn(' nonce="', challenge)

    def test_basic(self):
        basic = bytearray(f'{self.username}:{self.password}', 'utf-8')
        auth = 'Basic ' + base64.b64encode(basic).decode('ascii')

        response = self.client.get(self.url, secure=False, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401, 'Basic auth over HTTP protocol')

        response = self.client.get(self.url, secure=True, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200, 'Basic auth over HTTPS protocol')

    def test_another_auth(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Something else')
        self.assertEqual(response.status_code, 401)

    def test_digest__no_credentials(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Digest ')
        self.assertEqual(response.status_code, 401)

    def test_digest__missing_required(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Digest realm=""')
        self.assertEqual(response.status_code, 401)

    def test_digest__wrong_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url,
                                   algorithm='SHA-256')
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    def test_digest__wrong_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        auth = build_digest_header('another',
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    def test_digest__wrong_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'POST',  # wrong method
                                   '/test'  # wrong url
                                   )
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    def test_digest__wrong_password(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        auth = build_digest_header(self.username,
                                   'secret',
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    def test_digest__old_nonce(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertIn('WWW-Authenticate', response)
        challenge = parse_authorization_header(response['WWW-Authenticate'])

        old_ts = (now() - COLLECT_NONCE_LIFESPAN * 2).timestamp()
        realm = challenge['realm']

        _nonce_data = f'{old_ts}:{realm}:{settings.SECRET_KEY}'
        _nonce_data = md5_utf8(_nonce_data)
        nonce = f'{old_ts}:{_nonce_data}'

        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url,
                                   nonce=nonce)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401, auth)

    def test_access(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    def test_access__inactive(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)
        self.user.is_active = False
        self.user.save()
        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    def test_replay_attack(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertIn('WWW-Authenticate', response)

        auth_kwargs = {
            'username': self.username,
            'password': self.password,
            'challenge_header': response['WWW-Authenticate'],
            'method': 'GET',
            'path': self.url,
            'cnonce': hashlib.sha1(os.urandom(8)).hexdigest()[:16]
        }
        auth = build_digest_header(**auth_kwargs)

        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
        self.assertIn('WWW-Authenticate', response)

        for nonce_count in range(2, 4):
            auth = build_digest_header(nonce_count=nonce_count, **auth_kwargs)
            response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
            self.assertEqual(response.status_code, 200)


@override_settings(
    DEFAULT_REALM='digest',
    GATEWAY_ENABLED=False,
)
class MultitenancyAuthenticationTests(UrlsTestCase):

    def setUp(self):
        super(MultitenancyAuthenticationTests, self).setUp()

        # in aether.sdk.multitenancy.utils
        # def get_current_realm(request, default_realm=settings.DEFAULT_REALM):
        modules_sdk = [
            'aether.sdk.multitenancy.utils',
            'aether.sdk.auth.utils',
        ]
        for module_sdk in modules_sdk:
            reload(sys.modules[module_sdk])
            import_module(module_sdk)

        self.username = 'surveyor'
        self.password = '~t]:vS3Q>e{2k]CE'
        self.url = reverse('xform-list-xml')

        # The surveyor must be created using the serializer
        user = SurveyorSerializer(
            data={
                'username': self.username,
                'password': self.password,
            },
            context={'request': RequestFactory().get(self.url)},
        )
        self.assertTrue(user.is_valid(), user.errors)
        user.save()
        self.user = get_user_model().objects.get(pk=user.data['id'])
        self.assertEqual(self.user.username, f'{settings.DEFAULT_REALM}__{self.username}')
        self.assertTrue(self.user.groups.filter(name=settings.DEFAULT_REALM).exists())

    def test_challenge(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertIn('WWW-Authenticate', response)
        challenge = response['WWW-Authenticate']
        self.assertIn('Digest ', challenge)
        self.assertIn(f' realm="{COLLECT_REALM}"', challenge)
        self.assertIn(' qop="auth', challenge)
        self.assertIn(' algorithm="MD5"', challenge)
        self.assertIn(' stale="false"', challenge)
        self.assertIn(' opaque="', challenge)
        self.assertIn(' nonce="', challenge)

    def test__parsed_username(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.username,  # without realm prefix
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)

        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    def test__unparsed_username(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.user.username,  # with realm prefix
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)

        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    def test__no_realm(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)

        # remove user from default realm
        self.user.groups.filter(name=settings.DEFAULT_REALM).delete()

        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)


@override_settings(
    DEFAULT_REALM='digest',
    GATEWAY_ENABLED=True,
    GATEWAY_SERVICE_ID='odk',
    GATEWAY_PUBLIC_REALM='-',
    GATEWAY_PUBLIC_PATH='/-/odk',
    GATEWAY_HEADER_TOKEN='X-Oauth-Token',
)
class GatewayAuthenticationTests(UrlsTestCase):

    def setUp(self):
        super(GatewayAuthenticationTests, self).setUp()

        # in aether.sdk.multitenancy.utils
        # def get_current_realm(request, default_realm=settings.DEFAULT_REALM):
        modules_sdk = [
            'aether.sdk.multitenancy.utils',
            'aether.sdk.auth.utils',
        ]
        for module_sdk in modules_sdk:
            reload(sys.modules[module_sdk])
            import_module(module_sdk)

        self.username = 'surveyor'
        self.password = '~t]:vS3Q>e{2k]CE'

        self.url = reverse('xform-list-xml', kwargs={'realm': 'testing'})
        self.assertEqual(self.url, '/testing/odk/collect-test/formList')

        self.url_internal = reverse('xform-list-xml')
        self.assertEqual(self.url_internal, '/collect-test/formList')

        self.url_public = reverse('xform-list-xml', kwargs={'realm': '-'})
        self.assertEqual(self.url_public, '/-/odk/collect-test/formList')

        # belongs to "testing" realm
        user1 = SurveyorSerializer(
            data={
                'username': self.username,
                'password': self.password,
            },
            context={'request': RequestFactory().get(self.url)},
        )
        self.assertTrue(user1.is_valid(), user1.errors)
        user1.save()

        user_obj1 = get_user_model().objects.get(pk=user1.data['id'])
        self.assertNotEqual(user_obj1.username, 'digest__surveyor')
        self.assertEqual(user_obj1.username, 'testing__surveyor')
        self.assertFalse(user_obj1.groups.filter(name='digest').exists())
        self.assertTrue(user_obj1.groups.filter(name='testing').exists())

        # belongs to default realm "digest"
        user2 = SurveyorSerializer(
            data={
                'username': self.username,
                'password': self.password,
            },
            context={'request': RequestFactory().get(self.url_internal)},
        )
        self.assertTrue(user2.is_valid(), user2.errors)
        user2.save()

        user_obj2 = get_user_model().objects.get(pk=user2.data['id'])
        self.assertEqual(user_obj2.username, 'digest__surveyor')
        self.assertNotEqual(user_obj2.username, 'testing__surveyor')
        self.assertTrue(user_obj2.groups.filter(name='digest').exists())
        self.assertFalse(user_obj2.groups.filter(name='testing').exists())

    def test__access__with_realm_in_path__and_short_username(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)

        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['User'], 'testing__surveyor')

    def test__access__with_realm_in_path__and_long_username(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        auth = build_digest_header('testing__surveyor',
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url)

        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['User'], 'testing__surveyor')

    def test__access__without_realm_in_path__and_wrong_username(self):
        response = self.client.get(self.url_internal)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header('testing__surveyor',
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url_internal)

        response = self.client.get(self.url_internal, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    def test__access__without_realm_in_path__and_long_username(self):
        response = self.client.get(self.url_internal)
        self.assertEqual(response.status_code, 401)

        auth = build_digest_header('digest__surveyor',
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url_internal)

        response = self.client.get(self.url_internal, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['User'], 'digest__surveyor')

    def test__access__without_realm_in_path__and_short_username(self):
        response = self.client.get(self.url_internal)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url_internal)

        response = self.client.get(self.url_internal, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['User'], 'digest__surveyor')

    def test__access__with_public_realm_in_path__and_short_username(self):
        response = self.client.get(self.url_public)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   self.url_public)

        response = self.client.get(self.url_public, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['User'], 'digest__surveyor')

    def test__access__with_another_realm_in_path(self):
        url = reverse('xform-list-xml', kwargs={'realm': 'another'})
        self.assertEqual(url, '/another/odk/collect-test/formList')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(self.username,
                                   self.password,
                                   response['WWW-Authenticate'],
                                   'GET',
                                   url)

        response = self.client.get(url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
