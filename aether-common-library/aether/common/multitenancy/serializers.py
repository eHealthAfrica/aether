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

from rest_framework.serializers import PrimaryKeyRelatedField, ModelSerializer

from .utils import filter_by_realm, filter_users_by_realm


class MtModelSerializer(ModelSerializer):
    '''
    Overrides ``create`` method to add the new instance to the current realm.

    The ``settings.MULTITENANCY_MODEL`` serializer class must extend this one.
    '''

    def create(self, validated_data):
        instance = super(MtModelSerializer, self).create(validated_data)
        instance.add_to_realm(self.context['request'])
        return instance


class MtPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    '''
    Overrides ``get_queryset`` method to include filter by realm.

    Expects ``mt_field`` property.
    '''

    mt_field = None

    def __init__(self, **kwargs):
        self.mt_field = kwargs.pop('mt_field', self.mt_field)
        super(MtPrimaryKeyRelatedField, self).__init__(**kwargs)

    def get_queryset(self):
        qs = super(MtPrimaryKeyRelatedField, self).get_queryset()
        qs = filter_by_realm(self.context['request'], qs, self.mt_field)
        return qs


class MtUserRelatedField(PrimaryKeyRelatedField):
    '''
    Overrides ``get_queryset`` method to include filter by realm group.
    '''

    def get_queryset(self):
        qs = super(MtUserRelatedField, self).get_queryset()
        qs = filter_users_by_realm(self.context['request'], qs)
        return qs
