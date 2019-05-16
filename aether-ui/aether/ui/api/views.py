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

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from django_eha_sdk.multitenancy.views import MtViewSetMixin

from . import models, serializers, utils, kernel_utils


class ProjectViewSet(MtViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    ordering = ('name',)
    search_fields = ('name',)


class PipelineViewSet(MtViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Pipeline.objects.all()
    serializer_class = serializers.PipelineSerializer
    ordering = ('name',)
    pagination_class = None
    mt_field = 'project'

    @action(methods=['post'], detail=False)
    def fetch(self, request, *args, **kwargs):
        '''
        This endpoint fetches kernel artefacts and transforms them into UI models.

        Afterwards returns the list of pipelines.
        '''

        utils.kernel_artefacts_to_ui_artefacts(request)
        return self.list(request)


class ContractViewSet(MtViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    ordering = ('name',)
    mt_field = 'pipeline__project'

    @action(methods=['post'], detail=True)
    def publish(self, request, pk=None, *args, **kwargs):
        '''
        This endpoint transforms the supplied contract to kernel artefacts,
        publish and update the contract with the related kernel artefacts ids.

        Afterwards returns the contract.
        '''

        contract = self.get_object_or_404(pk=pk)
        try:
            utils.publish_contract(contract)
            return self.retrieve(request, pk)
        except utils.PublishError as pe:
            return Response(
                data={'detail': str(pe)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(methods=['get'], detail=True, url_path='publish-preflight')
    def publish_preflight(self, request, pk=None, *args, **kwargs):
        '''
        This endpoint checks if the contract is publishable
        and returns the list of failing reasons.
        '''

        contract = self.get_object_or_404(pk=pk)

        data = utils.publish_preflight(contract)
        return Response(data=data)


@api_view(['GET'])
def get_kernel_url(request, *args, **kwargs):
    return Response(kernel_utils.get_kernel_url(request))
