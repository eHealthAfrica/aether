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

from django.db import models as db_models
from django.db.models.functions import Cast, Coalesce
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404, get_list_or_404
from aether.sdk.multitenancy.utils import filter_by_realm, is_accessible_by_realm
from rest_framework.exceptions import PermissionDenied

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    renderer_classes,
)
from rest_framework.renderers import JSONRenderer

from aether.sdk.multitenancy.views import MtViewSetMixin
from aether.sdk.drf.views import FilteredMixin
from aether.python.avro.tools import random_avro, extract_jsonpaths_and_docs
from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    extract_create_entities,
)

from .constants import LINKED_DATA_MAX_DEPTH
from .entity_extractor import ExtractMixin
from .exporter import ExporterMixin
from .mapping_validation import validate_mappings

from . import filters, models, project_artefacts, serializers, utils


class ProjectViewSet(MtViewSetMixin, FilteredMixin, ExtractMixin, viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filterset_class = filters.ProjectFilter
    search_fields = ('name',)

    @action(detail=True, methods=['patch'], url_name='erase_data', url_path='delete-data')
    def delete_data(self, request, pk=None, *args, **kwargs):
        instance = self.get_object_or_404(pk=pk)
        try:
            instance.submissions.all().delete()
            instance.entities.all().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:  # pragma: no cover
            return Response(
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['get'], url_name='skeleton', url_path='schemas-skeleton')
    def schemas_skeleton(self, request, pk=None, *args, **kwargs):
        '''
        Returns the schemas "skeleton" used by this project.

        Reachable at ``/projects/{pk}/schemas-skeleton/?passthrough=true&family=<<string>>``

        These endpoints return the same result:

            ``/projects/{pk}/schemas-skeleton/?passthrough=true``
            ``/projects/{pk}/schemas-skeleton/?family={pk}``

        '''

        project = self.get_object_or_404(pk=pk)

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
            sd.schema
            for sd in project.schemadecorators.order_by('-created')
            if not family or sd.schema.family == family
        ]
        for schema in schemas:
            if not name:
                name = f'{project.name}-{schema.schema_name}'
            extract_jsonpaths_and_docs(
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
        schemas, schema decorators and mappings.

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
        and related artefacts: schema decorators and passthrough mappings.

        Returns the list of project and its affected artefact ids by type.

        Reachable at ``.../projects/{pk}/avro-schemas/``
        '''

        return self.__upsert_schemas(request, pk)

    def __retrieve_artefacts(self, request, pk=None):
        '''
        Returns the list of project and all its artefact ids by type.
        '''

        project = self.get_object_or_404(pk=pk)
        results = project_artefacts.get_project_artefacts(project)

        return Response(data=results)

    def __upsert_artefacts(self, request, pk=None):
        '''
        Creates or updates the project and its artefacts:
        schemas, schema decorators, mapping sets and mappings.

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
                # (schemadecorator entry)
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
        # check that the existent project is accessible
        self.get_object_or_403(pk=pk)

        data = request.data
        results = project_artefacts.upsert_project_artefacts(
            action=data.get('action', 'upsert'),
            project_id=pk,
            project_name=data.get('name'),
            schemas=data.get('schemas', []),
            mappingsets=data.get('mappingsets', []),
            mappings=data.get('mappings', []),
        )

        project = get_object_or_404(models.Project, pk=results['project'])
        project.add_to_realm(request)

        return Response(data=results)

    def __upsert_schemas(self, request, pk=None):
        '''
        Creates or updates the project and links it with the given AVRO schemas
        and related artefacts: schema decorators and passthrough mappings.

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
                # (schemadecorator entry) creating the passthrough mapping
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
        # check that the existent project is accessible
        self.get_object_or_403(pk=pk)

        data = request.data
        results = project_artefacts.upsert_project_with_avro_schemas(
            action=data.get('action', 'upsert'),
            project_id=pk,
            project_name=data.get('name'),
            avro_schemas=data.get('avro_schemas', []),
            family=data.get('family') or pk,
        )

        project = get_object_or_404(models.Project, pk=results['project'])
        project.add_to_realm(request)

        return Response(data=results)


class MappingSetViewSet(MtViewSetMixin, FilteredMixin, ExtractMixin, viewsets.ModelViewSet):
    queryset = models.MappingSet.objects.all()
    serializer_class = serializers.MappingSetSerializer
    filterset_class = filters.MappingSetFilter
    search_fields = ('name',)
    mt_field = 'project'

    @action(detail=True, methods=['post'], url_path='delete-artefacts')
    def delete_artefacts(self, request, pk=None, *args, **kwargs):
        mappingset = self.get_object_or_404(pk=pk)
        opts = request.data
        try:
            result = utils.bulk_delete_by_mappings(opts, pk)
            mappingset.delete()
            return Response(result)
        except Exception as e:  # pragma: no cover
            return Response(
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MappingViewSet(MtViewSetMixin, FilteredMixin, viewsets.ModelViewSet):
    queryset = models.Mapping.objects.all()
    serializer_class = serializers.MappingSerializer
    filterset_class = filters.MappingFilter
    search_fields = ('name',)
    mt_field = 'mappingset__project'

    @action(detail=True, methods=['post'], url_path='delete-artefacts')
    def delete_artefacts(self, request, pk=None, *args, **kwargs):
        mapping = self.get_object_or_404(pk=pk)
        opts = request.data
        try:
            result = utils.bulk_delete_by_mappings(opts, None, [pk])
            mapping.delete()
            return Response(result)
        except Exception as e:  # pragma: no cover
            return Response(
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['get'], url_path='topics')
    def topics(self, request, pk=None, *args, **kwargs):
        mapping = self.get_object_or_404(pk=pk)
        topics = mapping.schemadecorators.all().values_list('topic__name', flat=True).order_by()
        return Response(topics)


class SubmissionViewSet(MtViewSetMixin, FilteredMixin, ExtractMixin, ExporterMixin, viewsets.ModelViewSet):
    queryset = models.Submission.objects.all().prefetch_related('attachments')
    serializer_class = serializers.SubmissionSerializer
    filterset_class = filters.SubmissionFilter
    search_fields = ('project__name', 'mappingset__name',)
    mt_field = 'project'

    # Exporter required fields
    schema_field = 'mappingset__schema'
    schema_order = '-mappingset__created'
    attachment_field = 'attachments__id'
    attachment_parent_field = 'submission__id'

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            kwargs['many'] = isinstance(kwargs.get('data'), list)
        return super(SubmissionViewSet, self).get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        if (mappingset_id := request.GET.get('mappingset')):
            if isinstance(request.data, list):
                request._full_data = [
                    {
                        'mappingset': mappingset_id,
                        'payload': i
                    }
                    for i in request.data
                ]
            elif not request.data.get('mappingset'):
                request._full_data = {
                    'mappingset': mappingset_id,
                    'payload': request.data,
                }
        return super(SubmissionViewSet, self).create(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.bulk_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.bulk_update(request, *args, **kwargs)

    def bulk_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            # get instances in single SQL call
            instance = get_list_or_404(
                filter_by_realm(
                    request,
                    models.Submission.objects.all(),
                    self.mt_field,
                ),
                pk__in=[entry['id'] for entry in request.data]
            )

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    def check_realm_permission(self, request, mappingset):
        return is_accessible_by_realm(request, mappingset)

    @action(detail=False, methods=['post'])
    def validate(self, request, *args, **kwargs):
        '''
        Validates a submission payload using the provided mappingset id

        Reachable at ``POST /submissions/validate/``

        expected body:

            {
                'mappingset': 'uuid',
                'payload': {}
            }

        expected response:

        {
            # flag indicating if the submission is valid or not
            'is_valid': True|False,

            # list of entities successfully generated from the submitted payload
            'entities': [],

            # list of encountered errors
            aether_errors: []
        }
        '''

        mappingset_id = request.data.get('mappingset')
        payload = request.data.get('payload')
        if mappingset_id is None or payload is None:
            return Response(
                _('A mappingset id and payload must be provided'),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mappingset = get_object_or_404(models.MappingSet.objects.all(), pk=mappingset_id)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        if not self.check_realm_permission(request, mappingset):
            raise PermissionDenied(_('Not accessible by this realm'))

        mappings = mappingset.mappings.all()
        result = {
            'is_valid': True,
            'entities': [],
            ENTITY_EXTRACTION_ERRORS: []
        }
        for mapping in mappings:
            schemas = {
                sd.name: sd.schema.definition
                for sd in mapping.schemadecorators.all()
            }
            try:
                submission_data, entities = extract_create_entities(
                    submission_payload=payload,
                    mapping_definition=mapping.definition,
                    schemas=schemas,
                    mapping_id=mapping.id,
                )
                if submission_data.get(ENTITY_EXTRACTION_ERRORS):
                    result['is_valid'] = False
                    result[ENTITY_EXTRACTION_ERRORS] += submission_data[ENTITY_EXTRACTION_ERRORS]
                else:
                    result['entities'] += entities

            except Exception as e:  # pragma: no cover
                result['is_valid'] = False
                result[ENTITY_EXTRACTION_ERRORS].append(str(e))

        _status = status.HTTP_200_OK if result['is_valid'] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=_status)

    def destroy(self, request, pk=None, *args, **kwargs):
        '''
        Overrides the destroy method.

        Check parameter ``cascade`` and delete also the linked entities.
        '''

        if request.GET.get('cascade', 'false').lower() == 'true':
            instance = self.get_object_or_404(pk=pk)
            instance.entities.all().delete()

        return super(SubmissionViewSet, self).destroy(request, pk, *args, **kwargs)


class AttachmentViewSet(MtViewSetMixin, FilteredMixin, viewsets.ModelViewSet):
    queryset = models.Attachment.objects.all().prefetch_related('submission')
    serializer_class = serializers.AttachmentSerializer
    filterset_class = filters.AttachmentFilter
    search_fields = ('name',)
    mt_field = 'submission__project'

    @action(detail=True, methods=['get'])
    def content(self, request, pk=None, *args, **kwargs):
        attachment = self.get_object_or_404(pk=pk)
        return attachment.get_content()


class SchemaViewSet(FilteredMixin, viewsets.ModelViewSet):
    queryset = models.Schema.objects.all()
    serializer_class = serializers.SchemaSerializer
    filterset_class = filters.SchemaFilter
    search_fields = ('name',)

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

        extract_jsonpaths_and_docs(
            schema=schema.definition,
            jsonpaths=jsonpaths,
            docs=docs,
        )
        return Response(data={
            'jsonpaths': jsonpaths,
            'docs': docs,
            'name': schema.schema_name,
        })

    @action(detail=False, methods=['post'], url_path='unique-usage')
    def unique_usage(self, request, *args, **kwargs):
        '''
        Given a list of mapping ids, this view checks if a schema used in
        any of the supplied mappings is used outside the context of the mappings
        supplied

        Reached through POST '/schemas/unique-usage/'

        expected payload: [
            'mapping-1-uuid',
            'mapping-2-uuid',
            ...
        ]

        returned result: {
            # object with properties keys as schemas used in the context of supplied mappings
            # with values True|False
            # True if the schema is used only the the context and nowhere else
            # False if the schema is used by some other mapping
            # e.g

            Person : true

            # indicating the schema 'Person' is used by one or more
            # of the supplied mappings only
        }
        '''
        try:
            mappings = filter_by_realm(
                self.request,
                models.Mapping.objects.filter(pk__in=request.data or []),
                'mappingset__project'
            ).values_list('id', flat=True)
            return Response(utils.get_unique_schemas_used(mappings))
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SchemaDecoratorViewSet(MtViewSetMixin, FilteredMixin, viewsets.ModelViewSet):
    queryset = models.SchemaDecorator.objects.all()
    serializer_class = serializers.SchemaDecoratorSerializer
    filterset_class = filters.SchemaDecoratorFilter
    search_fields = ('name',)
    mt_field = 'project'

    @action(detail=True, methods=['get'])
    def skeleton(self, request, pk=None, *args, **kwargs):
        '''
        Returns the schema "skeleton".

        Reachable at ``/schemadecorators/{pk}/skeleton/``
        '''

        schema_decorator = self.get_object_or_404(pk=pk)
        schema = schema_decorator.schema

        # extract jsonpaths and docs from the schema definition
        jsonpaths = []
        docs = {}

        extract_jsonpaths_and_docs(
            schema=schema.definition,
            jsonpaths=jsonpaths,
            docs=docs,
        )
        return Response(data={
            'jsonpaths': jsonpaths,
            'docs': docs,
            'name': f'{schema_decorator.project.name}-{schema.schema_name}',
        })


class EntityViewSet(MtViewSetMixin, FilteredMixin, ExporterMixin, viewsets.ModelViewSet):
    queryset = models.Entity.objects.all().prefetch_related('submission__attachments')
    serializer_class = serializers.EntitySerializer
    filterset_class = filters.EntityFilter
    search_fields = ('project__name', 'schema__name',)
    mt_field = 'project'

    # Exporter required fields
    schema_field = 'schema__definition'
    schema_order = '-schema__created'
    attachment_field = 'submission__attachments__id'
    attachment_parent_field = 'submission__entities__id'

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            kwargs['many'] = isinstance(kwargs.get('data'), list)
        return super(EntityViewSet, self).get_serializer(*args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        def get_entity_linked_data(entity, request, resolved, depth, start_depth=0):
            if (start_depth >= depth):
                return resolved

            jsonld_field_names = [
                field['name']
                for field in entity.schemadecorator.schema.definition.get('fields')
                if field.get('jsonldPredicate')
            ]

            for field_name in jsonld_field_names:
                try:
                    linked_data_ref = entity.payload.get(field_name)
                    linked_entity = models.Entity.objects.filter(payload__id=linked_data_ref).first()
                    linked_entity_schema_name = linked_entity.schemadecorator.schema.name

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
            if depth > LINKED_DATA_MAX_DEPTH:
                # instead of raising an error change the value to the MAXIMUM
                depth = LINKED_DATA_MAX_DEPTH
        except Exception:
            depth = 0

        instance = self.get_object_or_404(pk=pk)
        try:
            if depth:
                instance.resolved = get_entity_linked_data(instance, request, {}, depth)
        except Exception:  # pragma: no cover
            instance.resolved = {}

        return Response(self.serializer_class(instance, context={'request': request}).data)


class SubmissionStatsMixin(MtViewSetMixin):
    search_fields = ('name',)
    ordering_fields = ('name', 'created',)
    ordering = ('name',)

    submissions_field = 'submissions'
    entities_fk = 'submission__mappingset'
    fields_list = ('id', 'name', 'created',)

    def get_queryset(self):
        def _get_list_param(name):
            value = self.request.query_params.get(name, '')
            return list(filter(None, value.split(',')))

        def _is_included(field_name):
            return (
                (not _fields or field_name in _fields) and
                (not _omit or field_name not in _omit)
            )

        qs = super(SubmissionStatsMixin, self).get_queryset()
        qs = qs.values(*self.fields_list)

        _fields = _get_list_param('fields')
        _omit = _get_list_param('omit')

        if _is_included('entities_count'):
            entities_sq = models.Entity.objects.filter(
                db_models.Q(**{self.entities_fk: db_models.OuterRef('pk')})
            )
            if self.request.query_params.get('passthrough', 'false').lower() == 'true':
                # filter entities generated by passthrough mappings
                # HOW: The schema family matches the project id

                # compare family with project id
                # (issue: need to cast the UUID field into a Text field)
                entities_sq = entities_sq.filter(
                    schema__family=Cast('project', db_models.TextField()),
                    mapping__is_read_only=True,
                )

            family = self.request.query_params.get('family')
            if family:
                entities_sq = entities_sq.filter(schema__family=family)

            entities_sq = entities_sq \
                .order_by() \
                .values(self.entities_fk) \
                .annotate(entities=db_models.Count('id', distinct=True)) \
                .values('entities')

            # Django ORM takes the subquery "group by" columns list to build the
            # main query "group by" columns list, this means that it includes
            # the subquery columns in the main query (obviously this fails
            # because the main query does not have access to them),
            # something like:
            #
            #    SELECT x, y, z,
            #          (SELECT ... FROM A, B, C WHERE ...) AS e
            #    FROM D
            #    WHERE ...
            #    GROUP BY D.x, D.y, D.z, A.a, B.b, C.c
            #
            # WORKAROUND: remove "group by" columns list
            def _get_group_by_cols(*args):  # pragma: no cover
                return []

            entities_sq = db_models.Subquery(
                queryset=entities_sq,
                output_field=db_models.IntegerField(),
            )
            entities_sq.contains_aggregate = True  # indicates that includes an aggregated value
            entities_sq.get_group_by_cols = _get_group_by_cols  # apply workaround

            qs = qs.annotate(entities_count=Coalesce(entities_sq, 0))

        if _is_included('first_submission'):
            qs = qs.annotate(
                first_submission=db_models.Min(f'{self.submissions_field}__created')
            )
        if _is_included('last_submission'):
            qs = qs.annotate(
                last_submission=db_models.Max(f'{self.submissions_field}__created')
            )
        if _is_included('submissions_count'):
            qs = qs.annotate(
                submissions_count=db_models.Count(f'{self.submissions_field}__id', distinct=True)
            )
        if _is_included('pending_submissions_count'):
            qs = qs.annotate(
                pending_submissions_count=db_models.Count(
                    f'{self.submissions_field}__id',
                    filter=db_models.Q(**{f'{self.submissions_field}__is_extracted': False}),
                    distinct=True,
                )
            )
        if _is_included('attachments_count'):
            qs = qs.annotate(
                attachments_count=db_models.Count(f'{self.submissions_field}__attachments__id', distinct=True)
            )

        return qs


class ProjectStatsViewSet(SubmissionStatsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectStatsSerializer
    filterset_class = filters.ProjectFilter
    search_fields = ('name',)
    entities_fk = 'project'
    fields_list = ('id', 'name', 'created', 'active',)


class MappingSetStatsViewSet(SubmissionStatsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.MappingSet.objects.all()
    serializer_class = serializers.MappingSetStatsSerializer
    filterset_class = filters.MappingSetFilter
    search_fields = ('name',)
    mt_field = 'project'


class ExportTaskViewSet(MtViewSetMixin, viewsets.ReadOnlyModelViewSet, mixins.DestroyModelMixin):
    queryset = models.ExportTask.objects.all()
    serializer_class = serializers.ExportTaskSerializer
    filterset_class = filters.ExportTaskFilter
    mt_field = 'project'

    @action(
        detail=True,
        methods=['get'],
        url_name='file_content',
        url_path='file-content/(?P<file_pk>[^/.]+)',
    )
    def file_content(self, request, pk=None, file_pk=None, *args, **kwargs):
        task = self.get_object_or_404(pk=pk)
        _file = task.files.get(pk=file_pk)
        return _file.get_content(as_attachment=True)


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([permissions.IsAuthenticated])
def validate_mappings_view(request, *args, **kwargs):
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
        submission_data, entities = extract_create_entities(
            submission_payload=submission_payload,
            mapping_definition=mapping_definition,
            schemas=schemas,
            mapping_id='validation',
        )
        validation_result = validate_mappings(
            submission_payload=submission_payload,
            schemas=schemas,
            mapping_definition=mapping_definition,
        )

        jsonpath_errors = [error._asdict() for error in validation_result]
        type_errors = submission_data[ENTITY_EXTRACTION_ERRORS]

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


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([permissions.IsAuthenticated])
def generate_avro_input(request, *args, **kwargs):
    '''
    Given a `schema` returns an input sample that conforms that schema.
    '''

    if 'schema' in request.data:
        schema = request.data['schema']
        input_sample = random_avro(schema)

        return Response({
            'schema': schema,
            'input': input_sample,
        })

    else:
        return Response(
            data={'message': _('Missing "schema" data')},
            status=status.HTTP_400_BAD_REQUEST,
        )
