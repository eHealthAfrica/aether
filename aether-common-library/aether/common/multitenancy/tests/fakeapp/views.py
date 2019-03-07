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

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from aether.common.multitenancy.views import MtViewSetMixin

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

    @action(detail=True, methods=['get'], url_path='custom-404')
    def custom_404(self, request, pk=None, *args, **kwargs):
        obj = self.get_object_or_404(pk=pk)
        return Response(data=self.serializer_class(obj, context={'request': request}).data)


class TestChildModelViewSet(MtViewSetMixin, ModelViewSet):
    queryset = TestChildModel.objects.order_by('name')
    serializer_class = TestChildModelSerializer
    mt_field = 'parent__mt'

    @action(detail=True, methods=['get'], url_path='custom-403')
    def custom_403(self, request, pk=None, *args, **kwargs):
        obj = self.get_object_or_403(pk=pk)

        if not obj:
            return Response(status=400)

        return Response(data=self.serializer_class(obj, context={'request': request}).data)
