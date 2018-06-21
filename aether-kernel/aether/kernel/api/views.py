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
import requests
import json

from django.db.models import Count, Min, Max
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from drf_openapi.views import SchemaView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from drf_openapi.views import SchemaView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from http import HTTPStatus
from django.http import HttpResponse

from aether.common.conf import settings as app_settings
from . import models, serializers, filters, constants, utils, mapping_validation, project_artefacts


def get_entity_linked_data(entity, request, resolved, depth, start_depth=0):
    while (start_depth < depth):
        start_depth = start_depth + 1
        schema_definition_fields = entity.projectschema.schema.definition['fields']
        jsonld_fields = [item for item in schema_definition_fields if item.get('jsonldPredicate')]
        for item in jsonld_fields:
            try:
                if item['jsonldPredicate'].get('_id'):
                    linked_data_ref = entity.payload.get(item['name'])
                    linked_entity = models.Entity.objects.filter(payload__id=linked_data_ref).first()
                    linked_entity_schema_name = linked_entity.projectschema.schema.name
                    if linked_entity_schema_name not in resolved:
                        resolved[linked_entity_schema_name] = {}
                    resolved[linked_entity_schema_name][linked_data_ref] = serializers.EntityLDSerializer(
                        linked_entity, context={'request': request}).data
                    get_entity_linked_data(linked_entity, request, resolved, depth, start_depth)
            except Exception:
                pass
    return resolved


class CustomViewSet(viewsets.ModelViewSet):

    @action(detail=True, methods=['get', 'post'])
    def details(self, request, pk=None, *args, **kwargs):
        '''
        Allow to retrieve data from a POST request.
        Reachable at ``.../{model}/{pk}/details/``
        '''

        return self.retrieve(request, pk, *args, **kwargs)

    @action(detail=False, methods=['get', 'post'])
    def fetch(self, request, *args, **kwargs):
        '''
        Allow to list data from a POST request.
        Reachable at ``.../{model}/fetch/``
        '''

        return self.list(request, *args, **kwargs)


class ProjectViewSet(CustomViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_class = filters.ProjectFilter

    @action(detail=True, methods=['get', 'patch'])
    def artefacts(self, request, pk=None, *args, **kwargs):
        '''
        Returns the list of project and its artefact ids by type.

        Reachable at ``.../projects/{pk}/artefacts/``
        '''

        if request.method == 'GET':
            return self.__retrieve_artefacts(request, pk)
        else:
            return self.__upsert_artefacts(request, pk)

    def __retrieve_artefacts(self, request, pk=None):
        '''
        Returns the list of project and all its artefact ids by type.
        '''

        project = get_object_or_404(models.Project, pk=pk)
        results = project_artefacts.get_project_artefacts(project)

        return Response(data=results)

    def __upsert_artefacts(self, request, pk=None):
        '''
        Creates or updates the project and its artefacts:
        schemas, project schemas and mappings.

        Returns the list of project and affected artefact ids by type.

        Indicating an ``id`` in any of the entries doesn't mean that
        the instance must exists, but in case of not, a new one with that
        id will be created.

        Expected payload:

            {
                # this is optional, if missing the method will assign a random name
                "name": "project name (optional but unique)",

                # this is optional, for each entry the method will
                # create/update a schema and also link it to the project
                # (projectschema entry)
                "schemas": [
                    {
                        "id": "schema id (optional)",
                        "name": "schema name (optional but unique)",
                        "definition": {
                            # the avro schema
                        },
                        "type": "record"
                    },
                    # ...
                ],

                # also optional
                "mappings": [
                    {
                        "id": "mapping id (optional)",
                        "name": "mapping name (optional but unique)",
                        # optional but nice to have
                        "definition": {
                            "mapping": [
                                # the mapping rules
                            ]
                        }
                    },
                    # ...
                ]
            }

        '''

        data = request.data
        results = project_artefacts.upsert_project_artefacts(
            project_id=pk,
            project_name=data.get('name'),
            schemas=data.get('schemas', []),
            mappings=data.get('mappings', []),
        )

        return Response(data=results)


class ProjectStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Project \
                     .objects \
                     .values('id', 'name', 'created') \
                     .annotate(
                         first_submission=Min('mappings__submissions__created'),
                         last_submission=Max('mappings__submissions__created'),
                         submission_count=Count('mappings__submissions__id'),
                     )
    serializer_class = serializers.ProjectStatsSerializer

    search_fields = ('name',)
    ordering_fields = ('name', 'created',)
    ordering = ('name',)


class MappingViewSet(CustomViewSet):
    queryset = models.Mapping.objects.all()
    serializer_class = serializers.MappingSerializer
    filter_class = filters.MappingFilter


class MappingStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Mapping \
                     .objects \
                     .values('id', 'name', 'created', 'definition') \
                     .annotate(
                         first_submission=Min('submissions__created'),
                         last_submission=Max('submissions__created'),
                         submission_count=Count('submissions__id'),
                     )
    serializer_class = serializers.MappingStatsSerializer

    search_fields = ('name',)
    ordering_fields = ('name', 'created',)
    ordering = ('name',)


class SubmissionViewSet(CustomViewSet):
    queryset = models.Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer
    filter_class = filters.SubmissionFilter


class AttachmentViewSet(CustomViewSet):
    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filter_class = filters.AttachmentFilter


class SchemaViewSet(CustomViewSet):
    queryset = models.Schema.objects.all()
    serializer_class = serializers.SchemaSerializer
    filter_class = filters.SchemaFilter


class ProjectSchemaViewSet(CustomViewSet):
    queryset = models.ProjectSchema.objects.all()
    serializer_class = serializers.ProjectSchemaSerializer
    filter_class = filters.ProjectSchemaFilter


class EntityViewSet(CustomViewSet):
    queryset = models.Entity.objects.all()
    serializer_class = serializers.EntitySerializer
    filter_class = filters.EntityFilter

    def retrieve(self, request, pk=None, *args, **kwargs):
        selected_record = get_object_or_404(models.Entity, pk=pk)
        depth = request.query_params.get('depth')
        if depth:
            try:
                depth = int(depth)
                if depth > constants.LINKED_DATA_MAX_DEPTH:
                    return Response({
                        'description': 'Supported max depth is 3'
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    selected_record.resolved = get_entity_linked_data(selected_record, request, {}, depth)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        serializer_class = serializers.EntitySerializer(selected_record, context={'request': request})
        return Response(serializer_class.data)


class AetherSchemaView(SchemaView):
    permission_classes = (permissions.AllowAny, )


def run_mapping_validation(submission_payload, mapping_definition, schemas):
    submission_data, entities = utils.extract_create_entities(
        submission_payload,
        mapping_definition,
        schemas,
    )
    validation_result = mapping_validation.validate_mappings(
        submission_payload=submission_payload,
        schemas=schemas,
        mapping_definition=mapping_definition,
    )
    jsonpath_errors = [error._asdict() for error in validation_result]
    type_errors = submission_data['aether_errors']
    return (
        jsonpath_errors + type_errors,
        entities,
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def setup_kong_consumer(request, *args, **kwargs):
    '''
    Create kong oauth2 credentials for authenticated user
    '''
    if 'username' in request.data and 'password' in request.data:
        url = 'http://' + app_settings.PROJECT_API_URL + ':8001/consumers/' + app_settings.KONG_CONSUMER + '/oauth2'
        if 'redirect_uri' in request.data:
            redirect_uri = request.data['redirect_uri']
        else:
            redirect_uri = 'http://' + app_settings.PROJECT_API_URL

        if 'app_name' in request.data:
            app_name = request.data['app_name']
        else:
            app_name = 'aether-app'

        jsonData = {
            'redirect_uri': redirect_uri,
            'name': app_name
        }
        results = HttpResponse(json.dumps({'description': 'Check that kong server is reachable'}),
                               content_type='application/json')
        results.status_code = 400
        try:
            results = requests.post(url, json=jsonData,
                                    headers={'Content-Type': 'application/json', 'apikey': app_settings.KONG_APIKEY})
            client_credentials_returned = json.loads(results.content)
            if 'client_id' in client_credentials_returned:
                client_credentials = {}
                client_credentials['provision_key'] = app_settings.KONG_OAUTH2_PROVISION_KEY
                client_credentials['grant_type'] = 'password'
                client_credentials['username'] = request.data['username']
                client_credentials['password'] = request.data['password']
                client_credentials['client_id'] = client_credentials_returned['client_id']
                client_credentials['client_secret'] = client_credentials_returned['client_secret']
                if 'authenticated_userid' in request.data:
                    client_credentials['authenticated_userid'] = request.data['authenticated_userid']
                else:
                    client_credentials['authenticated_userid'] = request.data['username']
                results = requests.post(app_settings.OAUTH2_TOKEN_URL, json=client_credentials, verify=False,
                                        headers={'Content-Type': 'application/json',
                                                 'apikey': app_settings.KONG_APIKEY})
            else:
                results = HttpResponse(json.dumps({'description': 'No client_id generated'}),
                                       content_type='application/json')
                results.status_code = 400
        except Exception as e:
            pass
        return HttpResponse(results)
    else:
        results = HttpResponse(json.dumps({'description': 'Missing username or password'}),
                               content_type='application/json')
        results.status_code = 400
        return results


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([permissions.IsAuthenticated])
def validate_mappings(request):
    '''
    Given a `submission_payload`, a `mapping_definition` and a list of
    `entities`, verify that each mapping function in `mapping_definition` can
    extract a value from `submission_payload` and assign it to at least one
    entity in `entities`.

    This endpoint is useful for clients who are in the process of
    developing an Aether solution but have not yet submitted any complete
    Project; using this endpoint, it is possible to check the mapping functions
    (jsonpaths) align with both the source (`submission_payload`) and the
    target (`entities`).
    '''
    serializer = serializers.MappingValidationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        errors, entities = run_mapping_validation(**serializer.data)
        return Response({
            'entities': [entity.payload for entity in entities],
            'mapping_errors': errors,
        })
    except Exception as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
