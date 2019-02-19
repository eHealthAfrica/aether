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

from rest_framework.viewsets import ModelViewSet

from aether.common.multitenancy.utils import MtViewSetMixin

from aether.common.multitenancy.tests.fakeapp.models import (
    TestModel,
    TestChildModel,
)
from aether.common.multitenancy.tests.fakeapp.serializers import (
    TestModelSerializer,
    TestChildModelSerializer,
)


class TestModelViewSet(MtViewSetMixin, ModelViewSet):
    queryset = TestModel.objects.order_by('name')
    serializer_class = TestModelSerializer
    # mt_field = 'mt'  # not needed in this case


class TestChildModelViewSet(MtViewSetMixin, ModelViewSet):
    queryset = TestChildModel.objects.order_by('name')
    serializer_class = TestChildModelSerializer
    mt_field = 'parent__mt'
