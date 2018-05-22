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

from django.db.models import Count, Min, Max

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from drf_openapi.views import SchemaView
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from http import HTTPStatus

from aether.kernel.settings import logger

from . import models, serializers, filters, constants, utils, mapping_validation


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
            except Exception as e:
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
        try:
            selected_record = models.Entity.objects.get(pk=pk)
        except Exception as e:
            return Response(str(e), status=HTTPStatus.NOT_FOUND)
        depth = request.query_params.get('depth')
        if depth:
            try:
                depth = int(depth)
                if depth > constants.LINKED_DATA_MAX_DEPTH:
                    return Response({
                        'description': 'Supported max depth is 3'
                    }, status=HTTPStatus.BAD_REQUEST)
                else:
                    selected_record.resolved = get_entity_linked_data(selected_record, request, {}, depth)
            except Exception as e:
                return Response(str(e), status=HTTPStatus.BAD_REQUEST)
        serializer_class = serializers.EntitySerializer(selected_record, context={'request': request})
        return Response(serializer_class.data, status=HTTPStatus.OK)


class AetherSchemaView(SchemaView):
    permission_classes = (permissions.AllowAny, )


def run_mapping_validation(submission_payload, mapping_definition, schemas):
    submission_data, entities = utils.extract_create_entities(
        submission_payload,
        mapping_definition,
        schemas,
    )
    jsonpath_errors = mapping_validation.validate_mappings(
        submission_payload=submission_payload,
        entities=entities,
        mapping_definition=mapping_definition,
    )
    type_errors = submission_data['aether_errors']
    return (
        # Only return jsonpath errors if no type errors are present.
        # Background: if we have any type errors, no meaningful jsonpath
        # validation could have taken place, since jsonpath validations were
        # run against invalid or absent entities/types.
        type_errors or jsonpath_errors,
        entities,
    )


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([IsAuthenticated])
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
        error = str(e)
        logger.exception(error)
        return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
