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

from django.conf import settings
from django.shortcuts import get_object_or_404

from http import HTTPStatus

from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from aether.common.kernel.utils import get_kernel_server_url

from . import models, serializers, utils


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = models.Pipeline.objects.all()
    serializer_class = serializers.PipelineSerializer
    ordering = ('name',)
    pagination_class = None

    @action(methods=['post'], detail=False)
    def fetch(self, request):
        '''
        This view gets kernel objects, transforms and loads into a pipeline
        '''

        utils.kernel_to_pipeline()
        return self.list(request)

    @action(methods=['post'], detail=True)
    def publish(self, request, pk=None):
        '''
        This view transforms the supplied pipeline to kernel artefacts,
        publish and update the pipeline/contract with related kernel artefacts ids.
        '''

        project_name = request.data.get('project_name', settings.APP_NAME)
        overwrite = request.data.get('overwrite', False)
        contract_id = request.data.get('contract_id')
        objects_to_overwrite = request.data.get('ids', {})

        try:
            contract = get_object_or_404(models.Contract, pk=contract_id)
        except Exception as e:
            return Response({'error': [str(e)]}, status=HTTPStatus.BAD_REQUEST)

        outcome = utils.publish_preflight(contract)
        if len(outcome.get('error', [])):
            return Response(outcome, status=HTTPStatus.BAD_REQUEST)

        publish_result = {}
        if len(outcome.get('exists', [])):
            if overwrite:
                publish_result = utils.publish_contract(project_name, contract, objects_to_overwrite)
            else:
                return Response(outcome, status=HTTPStatus.BAD_REQUEST)
        else:
            publish_result = utils.publish_contract(project_name, contract)

        if 'error' in publish_result:
            return Response(publish_result, status=HTTPStatus.BAD_REQUEST)

        return self.retrieve(request, pk)


class ContractViewSet(viewsets.ModelViewSet):
    queryset = models.Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    ordering = ('name',)


@api_view(['GET'])
def get_kernel_url(request):
    return Response(get_kernel_server_url())
