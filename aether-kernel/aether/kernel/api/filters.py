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

from django.db import models as django_models
import django_filters.rest_framework as filters

from . import models


class ProjectFilter(filters.FilterSet):
    schema = filters.CharFilter(
        name='projectschemas__schema',
        lookup_expr='exact',
    )

    class Meta:
        fields = '__all__'
        model = models.Project


class MappingFilter(filters.FilterSet):
    class Meta:
        exclude = ('definition',)
        model = models.Mapping


class SubmissionFilter(filters.FilterSet):
    instanceID = filters.CharFilter(
        name='payload__meta__instanceID',
        lookup_expr='exact',
    )
    project = filters.CharFilter(
        name='mapping__project',
        lookup_expr='exact',
    )
    filter_overrides = {
        django_models.DateTimeField: {
            'filter_class': filters.IsoDateTimeFilter
        },
    }

    class Meta:
        exclude = ('payload',)
        model = models.Submission
        fields = {
            'created': ('lt', 'gt', 'lte', 'gte'),
            'modified': ('lt', 'gt', 'lte', 'gte')
        }


class AttachmentFilter(filters.FilterSet):
    class Meta:
        exclude = ('attachment_file',)
        model = models.Attachment


class SchemaFilter(filters.FilterSet):
    project = filters.CharFilter(
        name='projectschemas__project',
        lookup_expr='exact',
    )

    class Meta:
        exclude = ('definition',)
        model = models.Schema


class ProjectSchemaFilter(filters.FilterSet):
    class Meta:
        fields = '__all__'
        model = models.ProjectSchema


class EntityFilter(filters.FilterSet):
    project = filters.CharFilter(
        name='projectschema__project',
        lookup_expr='exact',
    )
    schema = filters.CharFilter(
        name='projectschema__schema',
        lookup_expr='exact',
    )

    class Meta:
        exclude = ('payload',)
        model = models.Entity
