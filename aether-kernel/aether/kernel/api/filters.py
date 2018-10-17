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

import django_filters.rest_framework as filters
import uuid

from . import models


class ProjectFilter(filters.FilterSet):
    schema = filters.CharFilter(
        method='schema_filter',
    )

    def schema_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(projectschemas__schema__pk=value)
        else:
            return queryset.filter(projectschemas__schema__name=value)

    class Meta:
        fields = '__all__'
        model = models.Project


class MappingFilter(filters.FilterSet):
    mappingset = filters.CharFilter(
        method='mappingset_filter',
    )
    projectschema = filters.CharFilter(
        method='projectschema_filter',
    )

    def mappingset_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(mappingset__pk=value)
        else:
            return queryset.filter(mappingset__name=value)

    def projectschema_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(projectschemas__pk=value)
        else:
            return queryset.filter(projectschemas__name=value)

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
        fields = '__all__'
        exclude = ('payload',)
        model = models.Submission


class AttachmentFilter(filters.FilterSet):
    class Meta:
        exclude = ('attachment_file',)
        model = models.Attachment


class SchemaFilter(filters.FilterSet):
    project = filters.CharFilter(
        method='project_filter',
    )

    def project_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(projectschemas__project__pk=value)
        else:
            return queryset.filter(projectschemas__project__name=value)

    class Meta:
        exclude = ('definition',)
        model = models.Schema


class ProjectSchemaFilter(filters.FilterSet):
    mapping = filters.CharFilter(
        method='mapping_filter',
    )

    def mapping_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(mappings__pk=value)
        else:
            return queryset.filter(mappings__name=value)

    class Meta:
        fields = '__all__'
        model = models.ProjectSchema


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
        field_name='projectschema__schema__family',
        lookup_expr='iexact',  # case-insensitive
    )

    def project_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(project__pk=value)
        else:
            return queryset.filter(project__name=value)

    def schema_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(projectschema__schema__pk=value)
        else:
            return queryset.filter(projectschema__schema__name=value)

    def mapping_filter(self, queryset, name, value):
        if is_uuid(value):
            return queryset.filter(mapping__pk=value)
        else:
            return queryset.filter(mapping__name=value)

    class Meta:
        fields = '__all__'
        exclude = ('payload',)
        model = models.Entity


def is_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        # `value` is not a valid UUID
        return False
