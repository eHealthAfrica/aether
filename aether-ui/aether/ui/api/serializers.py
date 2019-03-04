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

from django.utils.translation import ugettext as _
from drf_dynamic_fields import DynamicFieldsMixin

from rest_framework import serializers

from . import models


class ContractSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='contract-detail',
    )

    pipeline_url = serializers.HyperlinkedRelatedField(
        read_only=True,
        source='pipeline',
        view_name='pipeline-detail',
    )

    def update(self, instance, validated_data):
        if instance.is_read_only:
            raise serializers.ValidationError({'detail': _('Contract is read only')})

        return super(ContractSerializer, self).update(instance, validated_data)

    class Meta:
        model = models.Contract
        fields = '__all__'


class PipelineSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='pipeline-detail',
    )

    contracts = ContractSerializer(many=True, read_only=True)

    project = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.Project.objects.all(),
    )

    def create(self, validated_data):
        if not validated_data.get('project'):
            # assign new pipelines to the default project
            default_project = models.Project.objects.filter(is_default=True).first()
            validated_data['project'] = default_project

        instance = super(PipelineSerializer, self).create(validated_data)

        # create initial contract
        models.Contract.objects.create(
            pk=instance.pk,      # re-use same uuid
            name=instance.name,  # re-use same name
            pipeline=instance,
        )

        return instance

    def update(self, instance, validated_data):
        if instance.contracts.filter(is_read_only=True).count() > 0:
            raise serializers.ValidationError({'detail': _('Pipeline is read only')})

        return super(PipelineSerializer, self).update(instance, validated_data)

    class Meta:
        model = models.Pipeline
        fields = '__all__'


class ProjectSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='project-detail',
    )

    pipelines = PipelineSerializer(many=True, read_only=True)

    class Meta:
        model = models.Project
        fields = '__all__'
