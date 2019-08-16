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

import base64
import hashlib
import os
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse

from ...tests import CustomTestCase
from ...serializers import SurveyorSerializer

from ..auth_utils import parse_authorization_header


def build_digest_header(
        username,
        password,
        challenge_header,
        method,
        path,
        nonce_count=1,
        cnonce=None,
        algorithm='MD5',
        qop='auth',
):
    challenge_data = parse_authorization_header(challenge_header)
    realm = challenge_data['realm']
    nonce = challenge_data['nonce']
    qop = challenge_data['qop']
    opaque = challenge_data['opaque']

    def md5_utf8(x):
        if isinstance(x, str):
            x = x.encode('utf-8')
        return hashlib.md5(x).hexdigest()

    def KD(s, d):
        return md5_utf8(f'{s}:{d}')

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
class AuthenticationTests(CustomTestCase):

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
        self.assertIn(' realm="collect@testserver"', challenge)
        self.assertIn(' qop="auth', challenge)
        self.assertIn(' algorithm="MD5"', challenge)
        self.assertIn(' stale="false"', challenge)
        self.assertIn(' opaque="', challenge)
        self.assertIn(' nonce="', challenge)

    def test_basic(self):
        basic = bytearray(f'{self.username}:{self.password}', 'utf-8')
        auth = 'Basic ' + base64.b64encode(basic).decode('ascii')

        response = self.client.get(self.url, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

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


class MultitenancyAuthenticationTests(CustomTestCase):

    def setUp(self):
        super(MultitenancyAuthenticationTests, self).setUp()

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
        self.assertIn(f' realm="{settings.DEFAULT_REALM}@testserver"', challenge)
        self.assertIn(' qop="auth', challenge)
        self.assertIn(' algorithm="MD5"', challenge)
        self.assertIn(' stale="false"', challenge)
        self.assertIn(' opaque="', challenge)
        self.assertIn(' nonce="', challenge)

    def test__parsed_username(self):
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

    def test__unparsed_username(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

        self.assertIn('WWW-Authenticate', response)
        auth = build_digest_header(f'{settings.DEFAULT_REALM}__{self.username}',
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
