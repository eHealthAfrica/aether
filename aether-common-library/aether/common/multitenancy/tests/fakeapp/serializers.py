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

from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

from aether.common.multitenancy.serializers import (
    MtModelSerializer,
    MtPrimaryKeyRelatedField,
    MtUserRelatedField,
)

from .models import TestModel, TestChildModel

UserModel = get_user_model()


class TestModelSerializer(MtModelSerializer):

    user = MtUserRelatedField(
        allow_null=True,
        default=None,
        queryset=UserModel.objects.all(),
    )

    class Meta:
        model = TestModel
        fields = '__all__'


class TestChildModelSerializer(ModelSerializer):

    parent = MtPrimaryKeyRelatedField(
        queryset=TestModel.objects.all(),
    )

    class Meta:
        model = TestChildModel
        fields = '__all__'


class TestUserSerializer(ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('id', 'username',)
