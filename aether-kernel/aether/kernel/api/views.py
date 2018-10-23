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

from django.db.models import Count, Min, Max, TextField, Q, Case, When
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import viewsets, permissions, status, versioning
from rest_framework.response import Response
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    renderer_classes,
)
from rest_framework.renderers import JSONRenderer

from . import (
    avro_tools,
    constants,
    exporter,
    filters,
    mapping_validation,
    models,
    project_artefacts,
    serializers,
    utils,
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_class = filters.ProjectFilter

    @action(detail=True, methods=['get'], url_name='skeleton', url_path='schemas-skeleton')
    def schemas_skeleton(self, request, pk=None, *args, **kwargs):
        '''
        Returns the schemas "skeleton" used by this project.

        Reachable at ``/projects/{pk}/schemas-skeleton/?passthrough=true&family=<<string>>``

        These endpoints return the same result:

            ``/projects/{pk}/schemas-skeleton/?passthrough=true``
            ``/projects/{pk}/schemas-skeleton/?family={pk}``

        '''

        project = get_object_or_404(models.Project, pk=pk)

        # extract jsonpaths and docs from linked schemas definition
        jsonpaths = []
        docs = {}
        name = None

        if request.query_params.get('passthrough', 'false') == 'true':
            # the passthrough schemas are identified with the project id
            family = str(project.id)
        else:
            family = request.query_params.get('family')

        schemas = [
            ps.schema
            for ps in project.projectschemas.order_by('-created')
            if not family or ps.schema.family == family
        ]
        for schema in schemas:
            if not name:
                name = f'{project.name}-{schema.schema_name}'
            avro_tools.extract_jsonpaths_and_docs(
                schema=schema.definition,
                jsonpaths=jsonpaths,
                docs=docs,
            )

        return Response(data={
            'jsonpaths': jsonpaths,
            'docs': docs,
            'name': name or project.name,
            'schemas': len(schemas),
        })

    @action(detail=True, methods=['get', 'patch'])
    def artefacts(self, request, pk=None, *args, **kwargs):
        '''
        PATCH: Creates or updates the project and its artefacts:
        schemas, project schemas and mappings.

        PATCH|GET: Returns the list of project and affected artefact ids by type.

        Reachable at ``/projects/{pk}/artefacts/``
        '''

        if request.method == 'GET':
            return self.__retrieve_artefacts(request, pk)
        else:
            return self.__upsert_artefacts(request, pk)

    @action(detail=True, methods=['patch'], url_path='avro-schemas')
    def avro_schemas(self, request, pk=None, *args, **kwargs):
        '''
        Creates or updates the project and links it with the given AVRO schemas
        and related artefacts: project schemas and passthrough mappings.

        Returns the list of project and its affected artefact ids by type.

        Reachable at ``.../projects/{pk}/avro-schemas/``
        '''

        return self.__upsert_schemas(request, pk)

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
        schemas, project schemas, mapping sets and mappings.

        Note: this method will never DELETE any artefact.

        Returns the list of project and affected artefact ids by type.

        Indicating an ``id`` in any of the entries doesn't mean that
        the instance must exists, but in case of not, a new one with that
        id will be created.

        Expected payload:

            {
                # this is optional, indicates the action to execute:
                #   "create", creates the missing objects but does not update the existing ones
                #   otherwise creates/updates the given objects
                'action': 'create|upsert',

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

                # this is also optional, contains the list of input samples
                # used to validate the mapping rules
                "mappingsets": [
                    {
                        "id": "mapping set id (optional)",
                        "name": "mapping set name (optional but unique)",
                        "schema": {
                            # the avro schema
                        },
                        "input": {
                            # sample
                        }
                    }
                ]

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
                        },
                        "is_read_only": true | false,
                        "is_active": true | false,

                        # used to link the mapping with its mapping set
                        "mappingset": "mapping set id",
                        # used only to create the mapping set (if missing)
                        "schema": {
                            # the avro schema
                        },
                        "input": {
                            # sample
                        }
                    },
                    # ...
                ]
            }

        '''

        data = request.data
        results = project_artefacts.upsert_project_artefacts(
            action=data.get('action', 'upsert'),
            project_id=pk,
            project_name=data.get('name'),
            schemas=data.get('schemas', []),
            mappingsets=data.get('mappingsets', []),
            mappings=data.get('mappings', []),
        )

        return Response(data=results)

    def __upsert_schemas(self, request, pk=None):
        '''
        Creates or updates the project and links it with the given AVRO schemas
        and related artefacts: project schemas and passthrough mappings.

        Returns the list of project and its affected artefact ids by type.

        Indicating an ``id`` in any of the entries doesn't mean that
        the instance must exists, but in case of not, a new one with that
        id will be created.

        Expected payload:

            {
                # this is optional, indicates the action to execute:
                #   "create", creates the missing objects but does not update the existing ones
                #   otherwise creates/updates the given objects
                'action': 'create|upsert',

                # this is optional, if missing the method will assign a random name
                "name": "project name (optional but unique)",

                # this is optional, all the schemas created/updated will
                # be assigned to this family
                # if none is indicated the project id will be used
                # to identify the passthrough schemas
                "family": "family name",

                # this is optional, for each entry the method will
                # create/update a schema and also link it to the project
                # (projectschema entry) creating the passthrough mapping
                "avro_schemas": [
                    {
                        "id": "schema id (optional and shared with ALL the linked artefacts)",
                        "definition": {
                            # the avro schema
                        }
                    },
                    # ...
                ],
            }

        '''

        data = request.data
        results = project_artefacts.upsert_project_with_avro_schemas(
            action=data.get('action', 'upsert'),
            project_id=pk,
            project_name=data.get('name'),
            avro_schemas=data.get('avro_schemas', []),
            family=data.get('family') or pk,
        )

        return Response(data=results)


class MappingSetViewSet(viewsets.ModelViewSet):
    queryset = models.MappingSet.objects.all()
    serializer_class = serializers.MappingSetSerializer
    filter_class = filters.MappingSetFilter


class MappingViewSet(viewsets.ModelViewSet):
    queryset = models.Mapping.objects.all()
    serializer_class = serializers.MappingSerializer
    filter_class = filters.MappingFilter


class SubmissionViewSet(exporter.ExporterViewSet):
    queryset = models.Submission.objects.all()
    serializer_class = serializers.SubmissionSerializer
    filter_class = filters.SubmissionFilter


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filter_class = filters.AttachmentFilter


class SchemaViewSet(viewsets.ModelViewSet):
    queryset = models.Schema.objects.all()
    serializer_class = serializers.SchemaSerializer
    filter_class = filters.SchemaFilter

    @action(detail=True, methods=['get'])
    def skeleton(self, request, pk=None, *args, **kwargs):
        '''
        Returns the schema "skeleton".

        Reachable at ``/schema/{pk}/skeleton/``
        '''

        schema = get_object_or_404(models.Schema, pk=pk)

        # extract jsonpaths and docs from the schema definition
        jsonpaths = []
        docs = {}

        avro_tools.extract_jsonpaths_and_docs(
            schema=schema.definition,
            jsonpaths=jsonpaths,
            docs=docs,
        )
        return Response(data={
            'jsonpaths': jsonpaths,
            'docs': docs,
            'name': schema.schema_name,
        })


class ProjectSchemaViewSet(viewsets.ModelViewSet):
    queryset = models.ProjectSchema.objects.all()
    serializer_class = serializers.ProjectSchemaSerializer
    filter_class = filters.ProjectSchemaFilter

    @action(detail=True, methods=['get'])
    def skeleton(self, request, pk=None, *args, **kwargs):
        '''
        Returns the schema "skeleton".

        Reachable at ``/projectschemas/{pk}/skeleton/``
        '''

        project_schema = get_object_or_404(models.ProjectSchema, pk=pk)
        schema = project_schema.schema

        # extract jsonpaths and docs from the schema definition
        jsonpaths = []
        docs = {}

        avro_tools.extract_jsonpaths_and_docs(
            schema=schema.definition,
            jsonpaths=jsonpaths,
            docs=docs,
        )
        return Response(data={
            'jsonpaths': jsonpaths,
            'docs': docs,
            'name': f'{project_schema.project.name}-{schema.schema_name}',
        })


class EntityViewSet(exporter.ExporterViewSet):
    queryset = models.Entity.objects.all()
    serializer_class = serializers.EntitySerializer
    filter_class = filters.EntityFilter

    # Exporter required fields
    schema_field = 'projectschema__schema__definition'
    schema_order = '-projectschema__schema__created'

    def retrieve(self, request, pk=None, *args, **kwargs):
        def get_entity_linked_data(entity, request, resolved, depth, start_depth=0):
            if (start_depth >= depth):
                return resolved

            jsonld_field_names = [
                field['name']
                for field in entity.projectschema.schema.definition.get('fields')
                if field.get('jsonldPredicate')
            ]

            for field_name in jsonld_field_names:
                try:
                    linked_data_ref = entity.payload.get(field_name)
                    linked_entity = models.Entity.objects.filter(payload__id=linked_data_ref).first()
                    linked_entity_schema_name = linked_entity.projectschema.schema.name

                    resolved[linked_entity_schema_name] = resolved.get(linked_entity_schema_name, {})
                    resolved[linked_entity_schema_name][linked_data_ref] = self.serializer_class(
                        linked_entity,
                        context={'request': request},
                    ).data

                    # continue with next nested level
                    get_entity_linked_data(linked_entity, request, resolved, depth, start_depth + 1)
                except Exception:  # pragma: no cover
                    pass
            return resolved

        try:
            depth = request.query_params.get('depth', '0')
            depth = int(depth)
            if depth < 0:
                depth = 0
            if depth > constants.LINKED_DATA_MAX_DEPTH:
                # instead of raising an error change the value to the MAXIMUM
                depth = constants.LINKED_DATA_MAX_DEPTH
        except Exception:
            depth = 0

        instance = get_object_or_404(models.Entity, pk=pk)
        try:
            if depth:
                instance.resolved = get_entity_linked_data(instance, request, {}, depth)
        except Exception as e:  # pragma: no cover
            instance.resolved = {}

        return Response(self.serializer_class(instance, context={'request': request}).data)


class SubmissionStatsMixin(object):

    search_fields = ('name',)
    ordering_fields = ('name', 'created',)
    ordering = ('name',)

    def get_queryset(self):
        entities_count = Count('submissions__entities__id', distinct=True)

        entities_filter = None
        if self.request.query_params.get('passthrough', 'false') == 'true':
            # filter entities generated by passthrough mappings
            # HOW: The schema family matches the project id

            # compare family with project id
            # (issue: need to cast the UUID field into a Text field)
            project_id = Cast('submissions__entities__projectschema__project', TextField())

            entities_filter = Q(
                submissions__entities__projectschema__schema__family=project_id,
                submissions__entities__mapping__is_read_only=True,
            )
        else:
            family = self.request.query_params.get('family')
            if family:
                entities_filter = Q(submissions__entities__projectschema__schema__family=family)

        if entities_filter:
            # Django 1: use Case+When
            entities_count = Count(
                expression=Case(When(entities_filter, then='submissions__entities__id')),
                distinct=True,
            )

            # Django 2: filter in Count
            # (replace code above with this block when we upgrade to Django 2)
            # entities_count = Count(
            #     expression='submissions__entities__id',
            #     distinct=True,
            #     filter=entities_filter,
            # )

        return self.model.objects \
                   .values('id', 'name', 'created') \
                   .annotate(
                       first_submission=Min('submissions__created'),
                       last_submission=Max('submissions__created'),
                       submissions_count=Count('submissions__id', distinct=True),
                       entities_count=entities_count,
                   )


class ProjectStatsViewSet(SubmissionStatsMixin, viewsets.ReadOnlyModelViewSet):
    model = models.Project  # required by SubmissionStatsMixin
    serializer_class = serializers.ProjectStatsSerializer


class MappingSetStatsViewSet(SubmissionStatsMixin, viewsets.ReadOnlyModelViewSet):
    model = models.MappingSet  # required by SubmissionStatsMixin
    serializer_class = serializers.MappingSetStatsSerializer


SchemaView = get_schema_view(
    openapi.Info(
        title='Aether API',
        default_version='v1',
    ),
    public=True,
    permission_classes=(permissions.AllowAny, ),
)


class AetherSchemaView(SchemaView):
    versioning_class = versioning.URLPathVersioning


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

        return jsonpath_errors + type_errors, entities

    instance = serializers.MappingValidationSerializer(data=request.data)
    if not instance.is_valid():
        return Response(instance.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        errors, entities = run_mapping_validation(**instance.data)
        return Response({
            'entities': [entity.payload for entity in entities],
            'mapping_errors': errors,
        })
    except Exception as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
