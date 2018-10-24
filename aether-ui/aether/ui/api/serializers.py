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

    class Meta:
        model = models.Contract
        fields = '__all__'


class PipelineSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        read_only=True,
        view_name='pipeline-detail',
    )

    contracts = ContractSerializer(many=True, read_only=True)

    def update(self, instance, validated_data):
        if instance.contracts.filter(is_read_only=True).count() > 0:
            raise serializers.ValidationError({'description': _('Input is readonly')})

        return super(PipelineSerializer, self).update(instance, validated_data)

    class Meta:
        model = models.Pipeline
        fields = '__all__'
