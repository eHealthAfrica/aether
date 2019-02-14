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

import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

from oauth2client import client, crypt
from rest_framework import viewsets, status
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
    throttle_classes,
)

from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from aether.common.multitenancy.utils import MtViewSetMixin

from .couchdb_file import load_backup_file
from .couchdb_helpers import create_db, create_or_update_user
from .models import Project, Schema, MobileUser, DeviceDB
from .serializers import ProjectSerializer, SchemaSerializer, MobileUserSerializer
from .kernel_utils import (
    propagate_kernel_project,
    propagate_kernel_artefacts,
    KernelPropagationError,
)

from ..settings import LOGGING_LEVEL


logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)


class ProjectViewSet(MtViewSetMixin, viewsets.ModelViewSet):
    '''
    Create new Project entries.
    '''

    queryset = Project.objects \
                      .prefetch_related('schemas') \
                      .order_by('name')
    serializer_class = ProjectSerializer
    search_fields = ('name',)

    @action(detail=True, methods=['patch'])
    def propagate(self, request, pk=None, *args, **kwargs):
        '''
        Creates a copy of the project in Aether Kernel server.

        Reachable at ``.../projects/{pk}/propagate/``
        '''

        project = get_object_or_404(Project, pk=pk)

        try:
            propagate_kernel_project(project=project, family=request.data.get('family'))
        except KernelPropagationError as kpe:
            return Response(
                data={'description': str(kpe)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return self.retrieve(request, pk, *args, **kwargs)


class SchemaViewSet(MtViewSetMixin, viewsets.ModelViewSet):
    '''
    Create new Schema entries providing the AVRO schema via file or raw data.
    '''

    queryset = Schema.objects.order_by('name')
    serializer_class = SchemaSerializer
    search_fields = ('name', 'avro_schema',)
    mt_field = 'project__mt'

    def get_queryset(self):
        queryset = self.queryset

        project_id = self.request.query_params.get('project_id', None)
        if project_id is not None:
            queryset = queryset.filter(project=project_id)

        return queryset

    @action(detail=True, methods=['patch'])
    def propagate(self, request, pk=None, *args, **kwargs):
        '''
        Creates the artefacts of the schema in Aether Kernel server.

        Reachable at ``.../schemas/{pk}/propagate/``
        '''

        schema = get_object_or_404(Schema, pk=pk)

        try:
            propagate_kernel_artefacts(schema=schema, family=request.data.get('family'))
        except KernelPropagationError as kpe:
            return Response(
                data={'description': str(kpe)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return self.retrieve(request, pk, *args, **kwargs)


class MobileUserViewSet(viewsets.ModelViewSet):
    '''
    Create new Mobile User entries.
    '''

    queryset = MobileUser.objects.order_by('email')
    serializer_class = MobileUserSerializer
    search_fields = ('email',)


# Sync credentials endpoint
# Needs to be open since the mobile app doesn't have any creds
# is throttled
@csrf_exempt
@api_view(http_method_names=['POST'])
@throttle_classes([AnonRateThrottle])
@authentication_classes([])
@permission_classes([])
def signin(request):
    '''
    Sync credentials endpoint.

    Allows only **POST** http method.
    `It's throttled. <http://www.django-rest-framework.org/api-guide/throttling/>`__
    Needs to be open since the mobile app doesn't have any aether credentials.

    **Steps**
    1. Checks internal ``GOOGLE_CLIENT_ID``.
       .. warning:: If missing responses **500 -- Internal server error**.

    2. Checks ``idToken`` parameter.
       .. warning:: If missing responses **400 -- Bad request**.

    3. Checks ``deviceId`` parameter.
       .. warning:: If missing responses **400 -- Bad request**.

    4. Verifies *ID token* against `GOOGLE API
       <https://console.developers.google.com/apis/credentials>`__
       and receives google user account data.
        .. warning:: If could not verify *ID token* responses **500 -- Internal server error**.
        .. warning:: If invalid *ID token* responses **401 -- Unauthorized**.

    5. Checks ``email`` in user account.
       .. warning:: If missing responses **500 -- Internal server error**.

    6. Checks if user account does exist and is therefore allowed to sync.
       .. warning:: If missing (was not added to :class:`aether.sync.api.models.MobileUser`)
                    responses **403 -- Forbidden**.

    7. Creates/Updates the CouchDB user of the mobile user and grants
       permissions to the device database.
       .. warning:: The same google user account cannot be shared among devices
                    at the same time because every time the device signs in,
                    it changes the user CouchDB credentials.
       .. note:: The same device can have different google user accounts.

    8. Creates the DeviceDB record and the CouchDB database if missing.

    9. Responses **201 -- Created** with a payload with this schema:
        * ``username`` -- CouchDB credentials: username.
        * ``password`` -- CouchDB credentials: password.
        * ``url``      -- CouchDB device database url.
        * ``db``       -- CouchDB device database name.
    '''

    if settings.GOOGLE_CLIENT_ID == '':
        msg = _('Server is missing google client id')
        logger.error(msg)
        return Response(msg, status.HTTP_500_INTERNAL_SERVER_ERROR)

    token = request.data.get('idToken', '')
    if token == '':
        msg = _('No "idToken" sent')
        logger.error(msg)
        return Response(msg, status.HTTP_400_BAD_REQUEST)

    device_id = request.data.get('deviceId', '')
    if device_id == '':
        msg = _('No "deviceId" sent')
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
        return Response(_('Could not verify ID token'), status.HTTP_500_INTERNAL_SERVER_ERROR)
    except crypt.AppIdentityError:
        msg = _('Invalid ID Token')
        logger.error(msg)
        return Response(msg, status.HTTP_401_UNAUTHORIZED)

    email = user_data.get('email', '')
    if email == '':
        msg = _('User data is missing email')
        logger.error(msg)
        return Response(msg, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Check if mobile user does exist and is therefore allowed to sync
    try:
        user = MobileUser.objects.get(email=email)
    except MobileUser.DoesNotExist:
        # This is a user that comes from our app, but is not added to MobileUser list
        # That should trigger a different error message on the device
        msg = _('Mobile user does not exist')
        logger.error(msg)
        return Response(msg, status.HTTP_403_FORBIDDEN)

    # Create/Update the couch user of the mobile user and give permissions to the device db
    try:
        couchdb_config = create_or_update_user(email, device_id)
    except ValueError as err:
        logger.exception(str(err))
        return Response(_('Creating credentials failed'), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Get/Create the device db record and couchdb db
    try:
        device_db = DeviceDB.objects.get(device_id=device_id)
    except DeviceDB.DoesNotExist:
        logger.info(_('Creating db for device {}').format(device_id))
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
        return Response(_('Creating couchdb db failed'), status.HTTP_500_INTERNAL_SERVER_ERROR)

    payload = {
        'username': couchdb_config['username'],
        'password': couchdb_config['password'],
        'db': device_db.db_name,
        'url': request.build_absolute_uri('/_couchdb/' + device_db.db_name),
    }
    return Response(payload, status.HTTP_201_CREATED)


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([IsAuthenticated, IsAdminUser])
def load_file(request):
    '''
    POST file content into CouchDB server.
    '''

    try:
        stats = load_backup_file(fp=request.FILES['file'])
        return Response(data=stats)

    except Exception as e:
        logger.exception(e)
        return Response(data={'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
