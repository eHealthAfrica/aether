# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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
from requests.exceptions import HTTPError

from aether.sdk.multitenancy.views import MtViewSetMixin

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

    @action(detail=True, methods=['post'], url_path='delete-artefacts')
    def delete_artefacts(self, request, pk=None, *args, **kwargs):
        pipeline = self.get_object_or_404(pk=pk)
        artefacts_result = {'not_published': True}
        if pipeline.mappingset:
            try:
                artefacts_result = utils.delete_operation(
                    f'mappingsets/{pipeline.mappingset}/delete-artefacts/',
                    request.data,
                    pipeline,
                )
                if not artefacts_result:
                    return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            pipeline.delete()

        return Response(artefacts_result)

    @action(detail=True, methods=['put'], url_path='rename')
    def rename(self, request, pk=None, *args, **kwargs):
        pipeline = self.get_object_or_404(pk=pk)
        pipeline.name = request.data.get('name', pipeline.name)
        pipeline.save()
        if pipeline.mappingset:
            try:
                utils.kernel_data_request(
                    url=f'mappingsets/{pipeline.mappingset}/',
                    method='patch',
                    data=request.data,
                    headers=utils.wrap_kernel_headers(pipeline),
                )
            except HTTPError as e:
                if e.response.status_code == status.HTTP_404_NOT_FOUND:
                    pipeline.mappingset = None
                    pipeline.save()

        return Response(
            data=self.serializer_class(pipeline, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


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

    @action(detail=True, methods=['post'], url_path='delete-artefacts')
    def delete_artefacts(self, request, pk=None, *args, **kwargs):
        contract = self.get_object_or_404(pk=pk)
        artefacts_result = {'not_published': True}
        if contract.mapping:
            try:
                artefacts_result = utils.delete_operation(
                    f'mappings/{contract.mapping}/delete-artefacts/',
                    request.data,
                    contract
                )
                if not artefacts_result:
                    return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            contract.delete()

        return Response(artefacts_result)


@api_view(['GET'])
def get_kernel_url(request, *args, **kwargs):
    return Response(kernel_utils.get_kernel_url(request))
