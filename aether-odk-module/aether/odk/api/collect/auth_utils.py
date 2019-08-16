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

import random
import time

from hashlib import md5
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import six
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import AuthenticationFailed

from aether.sdk.auth.utils import parse_username, unparse_username
from aether.sdk.multitenancy.utils import get_current_realm
from aether.odk.api.collect.models import DigestAuthCounter, DigestPartial

# https://docs.opendatakit.org/openrosa-authentication/

COLLECT_ALGORITHM = 'MD5'
COLLECT_QOP = 'auth'  # Quality Of Protection
COLLECT_REALM = 'collect'


_WWW_AUTHENTICATE = (
    'Digest'
    ' realm="{realm}",'
    f' qop="{COLLECT_QOP}",'
    ' nonce="{nonce}",'
    ' opaque="{opaque}",'
    f' algorithm="{COLLECT_ALGORITHM}",'
    ' stale="false"'
)

_REQUIRED_FIELDS = (
    'algorithm',
    'cnonce',
    'nc',
    'nonce',
    'opaque',
    'realm',
    'response',
    'uri',
    'username',
)


def get_www_authenticate_header(request):
    '''
    Builds the WWW-Authenticate response header
    '''

    realm = _get_digest_realm(request)

    opaque = ''.join([random.choice('0123456789ABCDEF') for x in range(32)])
    _nonce_data = f'{time.time()}:{realm}:{settings.SECRET_KEY}'
    nonce = _hash_fn(_nonce_data)

    return _WWW_AUTHENTICATE.format(nonce=nonce, opaque=opaque, realm=realm)


def save_partial_digest(request, user, raw_password):
    '''
    Saves the partial digest for the parsed username and the unparsed username
    '''
    def _save(username):
        ha1 = _create_HA1(username, realm, raw_password)
        try:
            partial = DigestPartial.objects.get(username=username, realm=realm)
            partial.digest = ha1
            partial.save()
        except ObjectDoesNotExist:
            DigestPartial.objects.create(username=username, realm=realm, digest=ha1)

    realm = _get_digest_realm(request)

    _save(parse_username(request, user.username))
    _save(unparse_username(request, user.username))


def parse_authorization_header(challenge):
    # Digest field1="***", field2="***", field3="***", ...
    auth_type, auth_info = challenge.split(None, 1)

    digest_auth = dict()
    for h in auth_info.split(','):
        key, value = h.split('=', 1)
        digest_auth[key.strip()] = (
            value[1:-1]
            if value and value[0] == value[-1] == '"'
            else value
        )

    return digest_auth


def check_authorization_header(request):
    '''
    The values of the opaque and algorithm fields must be those supplied
    in the WWW-Authenticate response header
    '''

    auth_header = request.META['HTTP_AUTHORIZATION']
    challenge = parse_authorization_header(auth_header)

    # check fields
    for field in _REQUIRED_FIELDS:
        if field not in challenge:
            raise AuthenticationFailed(_('Required field "{}" not found').format(field))

    realm = _get_digest_realm(request)

    # validate field values
    values = {'algorithm': COLLECT_ALGORITHM, 'qop': COLLECT_QOP, 'realm': realm}
    for field in ('algorithm', 'qop', 'realm'):
        if challenge[field] != values[field]:
            raise AuthenticationFailed(_('Supplied field "{}" does not match').format(field))

    if unquote(urlparse(challenge['uri']).path) != request.path:
        raise AuthenticationFailed(_('Supplied field "{}" does not match').format('uri'))

    # check nonce counter
    try:
        auth_counter = DigestAuthCounter.objects.get(
            server_nonce=challenge['nonce'],
            client_nonce=challenge['cnonce'],
        )
        last_counter = auth_counter.client_counter
    except ObjectDoesNotExist:
        last_counter = None

    current_counter = int(challenge['nc'], 16)
    if last_counter is not None and not last_counter < current_counter:
        raise AuthenticationFailed(_(
            'Attempt to establish a previously used nonce counter'
        ))

    else:
        auth_counter, __ = DigestAuthCounter.objects.get_or_create(
            server_nonce=challenge['nonce'],
            client_nonce=challenge['cnonce'],
        )
        auth_counter.client_counter = current_counter
        auth_counter.save()

    username = challenge['username']
    try:
        partial = DigestPartial.objects.get(username=username, realm=realm)
        user = get_user_model().objects.get(username=parse_username(request, username))
    except ObjectDoesNotExist:
        raise AuthenticationFailed(_('Invalid username'))

    # check header response
    response_hash = _generate_response(request, partial.digest, challenge)
    if response_hash != challenge['response']:
        raise AuthenticationFailed(_('Invalid digest header'))

    return user


################################################################################
# Helpers

def _get_digest_realm(request):
    '''
    A string to be displayed to users so they know which username and
    password to use.

    Compliant with RFC 7616 (https://tools.ietf.org/html/rfc7616#section-3.3).
    '''

    url_info = urlparse(request.build_absolute_uri())
    realm = get_current_realm(request) or COLLECT_REALM

    return f'{realm}@{url_info.hostname}'


def _generate_response(request, ha1, challenge):
    '''
    Compile digest challenge response

    RESPONSE = HASH(HA1:nonce:nc:cnonce:qop:HA2)
    '''

    ha2 = _create_HA2(request.method, challenge['uri'])
    response_data = ':'.join((
        ha1,
        challenge['nonce'], challenge['nc'], challenge['cnonce'], COLLECT_QOP,
        ha2
    ))
    return _hash_fn(response_data)


def _create_HA1(username, realm, password):
    '''
    Create HA1 hash

    HA1 = HASH(username:realm:password)
    '''

    return _hash_fn(':'.join((username, realm, password)))


def _create_HA2(method, uri):
    '''
    Create HA2 hash

    HA2 = HASH(request-method:digest-URI)
    '''

    return _hash_fn(':'.join((method, uri)))


def _hash_fn(data):
    return md5(six.b(data)).hexdigest()
