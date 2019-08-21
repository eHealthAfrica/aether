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

import datetime
import logging
import random

from hashlib import md5
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import six
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import AuthenticationFailed

from aether.sdk.auth.utils import parse_username, unparse_username
from aether.odk.api.collect.models import DigestCounter, DigestPartial

# https://docs.opendatakit.org/openrosa-authentication/

COLLECT_ALGORITHM = 'MD5'
COLLECT_QOP = 'auth'  # Quality Of Protection
COLLECT_REALM = 'collect@aether.odk'
COLLECT_NONCE_LIFESPAN = datetime.timedelta(days=1)


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

MSG_MISSING = _('Required field "{}" not found')
MSG_WRONG = _('Supplied field "{}" does not match')
MSG_COUNTER = _('Attempt to establish a previously used nonce counter')
MSG_USERNAME = _('Invalid username')
MSG_HEADER = _('Invalid digest header')

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


def get_www_authenticate_header(request):
    '''
    Builds the WWW-Authenticate response header
    '''

    opaque = ''.join([random.choice('0123456789ABCDEF') for x in range(32)])
    nonce = _create_nonce(now().timestamp(), COLLECT_REALM)

    return _WWW_AUTHENTICATE.format(nonce=nonce, opaque=opaque, realm=COLLECT_REALM)


def save_partial_digest(request, user, raw_password):
    '''
    Saves the partial digest for the parsed/unparsed username
    '''
    def _save(username):
        ha1 = _create_HA1(username, COLLECT_REALM, raw_password)
        try:
            partial = DigestPartial.objects.get(user=user, username=username)
            partial.digest = ha1
            partial.save()
        except ObjectDoesNotExist:
            DigestPartial.objects.create(user=user, username=username, digest=ha1)

    _save(parse_username(request, user.username))
    _save(unparse_username(request, user.username))


def parse_authorization_header(challenge):
    # Digest field1="***", field2="***", field3="***", ...
    auth_type, auth_info = challenge.split(None, 1)

    challenge = dict()
    for h in auth_info.split(','):
        key, value = h.split('=', 1)
        challenge[key.strip()] = (
            value[1:-1]
            if value and value[0] == value[-1] == '"'
            else value
        )

    return challenge


def check_authorization_header(request):
    auth_header = request.META['HTTP_AUTHORIZATION']
    challenge = parse_authorization_header(auth_header)
    lifespan = now() - COLLECT_NONCE_LIFESPAN

    # remove old counters before checking them
    DigestCounter.objects.filter(modified__lte=lifespan).delete()

    # check fields
    for field in _REQUIRED_FIELDS:
        if field not in challenge:
            msg = MSG_MISSING.format(field)
            logger.error(msg)
            raise AuthenticationFailed(msg)

    # check field values
    timestamp, __ = challenge['nonce'].split(':', 1)
    expected_values = {
        'algorithm': COLLECT_ALGORITHM,
        'nonce': _create_nonce(timestamp, COLLECT_REALM),
        'qop': COLLECT_QOP,
        'realm': COLLECT_REALM,
    }
    for field in ('algorithm', 'nonce', 'qop', 'realm'):
        if challenge[field] != expected_values[field]:
            msg = MSG_WRONG.format(field)
            logger.error(msg)
            raise AuthenticationFailed(msg)

    # check URI
    if unquote(urlparse(challenge['uri']).path) != request.path:
        msg = MSG_WRONG.format('uri')
        logger.error(msg)
        raise AuthenticationFailed(msg)

    # SECURITY ENHANCEMENT: check if the nonce timepstamp is not older than ...
    if float(timestamp) <= lifespan.timestamp():
        msg = MSG_WRONG.format('nonce')
        logger.error(msg)
        raise AuthenticationFailed(msg)

    # check nonce counter
    try:
        auth_counter = DigestCounter.objects.get(
            server_nonce=challenge['nonce'],
            client_nonce=challenge['cnonce'],
        )
        last_counter = auth_counter.client_counter
    except ObjectDoesNotExist:
        last_counter = None

    current_counter = int(challenge['nc'], 16)
    if last_counter is not None and last_counter >= current_counter:
        logger.error(MSG_COUNTER)
        raise AuthenticationFailed(MSG_COUNTER)

    else:
        auth_counter, __ = DigestCounter.objects.get_or_create(
            server_nonce=challenge['nonce'],
            client_nonce=challenge['cnonce'],
        )
        auth_counter.client_counter = current_counter
        auth_counter.save()

    # check username
    username = challenge['username']
    try:
        user = get_user_model().objects.get(username=parse_username(request, username))
        partial = DigestPartial.objects.get(user=user, username=username)
    except ObjectDoesNotExist:
        logger.error(MSG_USERNAME)
        raise AuthenticationFailed(MSG_USERNAME)

    # check header response
    response_hash = _generate_response(request, partial.digest, challenge)
    if response_hash != challenge['response']:
        logger.error(MSG_HEADER)
        raise AuthenticationFailed(MSG_HEADER)

    return user


################################################################################
# Helpers

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


def _create_nonce(timestamp, realm):
    _nonce_data = f'{timestamp}:{realm}:{settings.SECRET_KEY}'
    return f'{timestamp}:{_hash_fn(_nonce_data)}'


def _hash_fn(data):
    return md5(six.b(data)).hexdigest()
