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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from oauth2client import client, crypt
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
    throttle_classes
)
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response


from .couchdb_helpers import create_db, create_or_update_user
from .models import MobileUser, DeviceDB

from ..settings import logger


# Sync credentials endpoint
# Needs to be open since the mobile app doesn't have any creds
# is throttled
@csrf_exempt
@api_view(http_method_names=['POST'])
@throttle_classes([AnonRateThrottle])
@authentication_classes([])
@permission_classes([])
def signin(request):
    if settings.GOOGLE_CLIENT_ID == '':
        msg = 'Server is missing google client id'
        logger.error(msg)
        return Response(msg, status.HTTP_500_INTERNAL_SERVER_ERROR)

    token = request.data.get('idToken', '')
    if token == '':
        msg = 'No "idToken" sent'
        logger.error(msg)
        return Response(msg, status.HTTP_400_BAD_REQUEST)

    device_id = request.data.get('deviceId', '')
    if device_id == '':
        msg = 'No "deviceId" sent'
        logger.error(msg)
        return Response(msg, status.HTTP_400_BAD_REQUEST)

    # decrypt JWT token,
    # check signature against google's certs
    # checks that the token was generated for our clientId
    try:
        user_data = client.verify_id_token(
            token,
            settings.GOOGLE_CLIENT_ID
        )
    except client.VerifyJwtTokenError as err:
        logger.exception(str(err))
        return Response('Could not verify ID token', status.HTTP_500_INTERNAL_SERVER_ERROR)
    except crypt.AppIdentityError:
        msg = 'Invalid ID Token'
        logger.error(msg)
        return Response(msg, status.HTTP_401_UNAUTHORIZED)

    email = user_data.get('email', '')
    if email == '':
        msg = 'User data is missing email'
        logger.error(msg)
        return Response(msg, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Check if mobile user does exist and is therefore allowed to sync
    try:
        user = MobileUser.objects.get(email=email)
    except MobileUser.DoesNotExist:
        # This is a user that comes from our app, but is not added to MobileUser list
        # That should trigger a different error message on the device
        msg = 'Mobile user does not exist'
        logger.error(msg)
        return Response(msg, status.HTTP_403_FORBIDDEN)

    # Create/Update the couch user of the mobile user and give permissions to the device db
    try:
        couchdb_config = create_or_update_user(email, device_id)
    except ValueError as err:
        logger.exception(str(err))
        return Response('Creating credentials failed', status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Get/Create the device db record and couchdb db
    try:
        device_db = DeviceDB.objects.get(device_id=device_id)
    except DeviceDB.DoesNotExist:
        logger.info('Creating db for device {}'.format(device_id))
        device_db = DeviceDB(device_id=device_id, mobileuser=user)
        device_db.save()
    else:
        device_db.mobileuser = user
        device_db.save()

    # Create couchdb for device
    try:
        create_db(device_id)
    except Exception as err:
        logger.exception(str(err))
        return Response('Creating couchdb db failed', status.HTTP_500_INTERNAL_SERVER_ERROR)

    payload = {
        'username': couchdb_config['username'],
        'password': couchdb_config['password'],
        # Send the url of the couchdb device-db for replication
        # 'url': 'http://localhost:8667/_couchdb/' + device_db.db_name
        'db': device_db.db_name,
        'url': request.build_absolute_uri('/_couchdb/' + device_db.db_name),
    }
    return Response(payload, status.HTTP_201_CREATED)
