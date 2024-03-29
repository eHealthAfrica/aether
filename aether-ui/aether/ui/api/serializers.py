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

from django.utils.translation import gettext as _
from drf_dynamic_fields import DynamicFieldsMixin

from rest_framework import serializers

from aether.sdk.drf.serializers import (
    DynamicFieldsModelSerializer,
    HyperlinkedIdentityField,
    HyperlinkedRelatedField,
)
from aether.sdk.multitenancy.serializers import (
    MtPrimaryKeyRelatedField,
    MtModelSerializer,
)

from . import models
from .utils import get_default_project


class ContractSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='contract-detail')
    pipeline_url = HyperlinkedRelatedField(
        view_name='pipeline-detail',
        read_only=True,
        source='pipeline',
    )

    def update(self, instance, validated_data):
        if instance.is_read_only:
            raise serializers.ValidationError({'detail': _('Contract is read only')})

        return super(ContractSerializer, self).update(instance, validated_data)

    class Meta:
        model = models.Contract
        fields = '__all__'


class PipelineSerializer(DynamicFieldsMixin, DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='pipeline-detail')

    contracts = ContractSerializer(many=True, read_only=True)
    is_read_only = serializers.BooleanField(read_only=True)

    project = MtPrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        required=False,
        style={'base_template': 'input.html'},
    )

    def create(self, validated_data):
        if not validated_data.get('project'):
            # assign new pipelines to the default project
            default_project = get_default_project(self.context['request'])
            validated_data['project'] = default_project

        instance = super(PipelineSerializer, self).create(validated_data)

        return instance

    def update(self, instance, validated_data):
        if instance.is_read_only:
            raise serializers.ValidationError({'detail': _('Pipeline is read only')})

        return super(PipelineSerializer, self).update(instance, validated_data)

    class Meta:
        model = models.Pipeline
        fields = '__all__'


class ProjectSerializer(DynamicFieldsMixin, MtModelSerializer):

    url = HyperlinkedIdentityField(view_name='project-detail')

    pipelines = PipelineSerializer(many=True, read_only=True)

    class Meta:
        model = models.Project
        fields = '__all__'
