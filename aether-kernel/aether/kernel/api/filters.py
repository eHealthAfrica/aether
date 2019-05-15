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

from django.db.models import TextField
from django.db.models.functions import Cast

import django_filters.rest_framework as filters
import uuid

from . import models


class ProjectFilter(filters.FilterSet):
    schema = filters.CharFilter(
        method='schema_filter',
    )

    def schema_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(schemadecorators__schema__pk=value)
        else:
            return queryset.filter(schemadecorators__schema__name=value)

    class Meta:
        fields = '__all__'
        model = models.Project


class MappingFilter(filters.FilterSet):
    mappingset = filters.CharFilter(
        method='mappingset_filter',
    )
    schemadecorator = filters.CharFilter(
        method='schemadecorator_filter',
    )

    def mappingset_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(mappingset__pk=value)
        else:
            return queryset.filter(mappingset__name=value)

    def schemadecorator_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(schemadecorators__pk=value)
        else:
            return queryset.filter(schemadecorators__name=value)

    class Meta:
        fields = '__all__'
        exclude = ('definition',)
        model = models.Mapping


class MappingSetFilter(filters.FilterSet):
    project = filters.CharFilter(
        method='project_filter',
    )

    def project_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(project__pk=value)
        else:
            return queryset.filter(project__name=value)

    class Meta:
        fields = '__all__'
        exclude = ('input', 'schema',)
        model = models.MappingSet


class SubmissionFilter(filters.FilterSet):
    project = filters.CharFilter(
        method='project_filter',
    )
    mappingset = filters.CharFilter(
        method='mappingset_filter',
    )

    def project_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(project__pk=value)
        else:
            return queryset.filter(project__name=value)

    def mappingset_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(mappingset__pk=value)
        else:
            return queryset.filter(mappingset__name=value)

    class Meta:
        exclude = ('payload',)
        model = models.Submission
        filter_overrides = {
            model.created: {
                'filter_class': filters.IsoDateTimeFilter
            },
        }
        # since we can't use __all__ and then extend the syntax on specific
        # fields, we have to enumerate all fields and give them the exact
        # filter
        fields = {str(k.name): ('exact',)
                  for k in model._meta.get_fields()
                  if k.name not in ['payload']}  # exclude not accessible from here
        fields['created'] = ('lt', 'gt', 'lte', 'gte', 'exact',)
        fields['modified'] = ('lt', 'gt', 'lte', 'gte', 'exact',)


class AttachmentFilter(filters.FilterSet):
    class Meta:
        exclude = ('attachment_file',)
        model = models.Attachment


class SchemaFilter(filters.FilterSet):
    project = filters.CharFilter(
        method='project_filter',
    )
    mapping = filters.CharFilter(
        method='mapping_filter',
    )

    def project_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(schemadecorators__project__pk=value)
        else:
            return queryset.filter(schemadecorators__project__name=value)

    def mapping_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(schemadecorators__mappings__pk=value)
        else:
            return queryset.filter(schemadecorators__mappings__name=value)

    class Meta:
        exclude = ('definition',)
        model = models.Schema


class SchemaDecoratorFilter(filters.FilterSet):
    mapping = filters.CharFilter(
        method='mapping_filter',
    )

    def mapping_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(mappings__pk=value)
        else:
            return queryset.filter(mappings__name=value)

    class Meta:
        exclude = ('topic_name',)
        model = models.SchemaDecorator


class EntityFilter(filters.FilterSet):
    schema = filters.CharFilter(
        method='schema_filter',
    )
    project = filters.CharFilter(
        method='project_filter',
    )
    mapping = filters.CharFilter(
        method='mapping_filter',
    )
    family = filters.CharFilter(
        field_name='schemadecorator__schema__family',
        lookup_expr='iexact',  # case-insensitive
    )
    passthrough = filters.CharFilter(
        method='passthrough__filter',
    )

    def project_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(project__pk=value)
        else:
            return queryset.filter(project__name=value)

    def schema_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(schemadecorator__schema__pk=value)
        else:
            return queryset.filter(schemadecorator__schema__name=value)

    def mapping_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(mapping__pk=value)
        else:
            return queryset.filter(mapping__name=value)

    def passthrough__filter(self, queryset, name, value):
        if value == 'true':
            return queryset.filter(
                schemadecorator__schema__family=Cast('project__pk', TextField()),
                mapping__is_read_only=True,
            )
        return queryset

    class Meta:
        exclude = ('payload',)
        model = models.Entity
        filter_overrides = {
            model.created: {
                'filter_class': filters.IsoDateTimeFilter
            },
        }
        # since we can't use __all__ and then extend the syntax on specific
        # fields, we have to enumerate all fields and give them the exact
        # filter
        fields = {str(k.name): ('exact',)
                  for k in model._meta.get_fields()
                  if k.name not in ['payload']}  # exclude not accessible from here
        fields['created'] = ('lt', 'gt', 'lte', 'gte', 'exact',)
        fields['modified'] = ('lt', 'gt', 'lte', 'gte', 'exact',)


def is_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        # `value` is not a valid UUID
        return False
