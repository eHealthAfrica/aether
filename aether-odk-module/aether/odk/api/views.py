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
from rest_framework.decorators import action
from rest_framework.response import Response

from aether.common.multitenancy.views import MtViewSetMixin, MtUserViewSetMixin

from .models import Project, XForm, MediaFile
from .serializers import (
    ProjectSerializer,
    MediaFileSerializer,
    SurveyorSerializer,
    XFormSerializer,
)
from .kernel_utils import (
    propagate_kernel_project,
    propagate_kernel_artefacts,
    KernelPropagationError,
)
from .surveyors_utils import get_surveyors


class ProjectViewSet(MtViewSetMixin, viewsets.ModelViewSet):
    '''
    Create new Project entries.
    '''

    queryset = Project.objects \
                      .prefetch_related('xforms', 'xforms__media_files') \
                      .order_by('name')
    serializer_class = ProjectSerializer
    search_fields = ('name',)

    @action(detail=True, methods=['patch'])
    def propagate(self, request, pk=None, *args, **kwargs):
        '''
        Creates a copy of the project in Aether Kernel server.

        Reachable at ``.../projects/{pk}/propagate/``
        '''

        project = self.get_object_or_404(pk=pk)

        try:
            propagate_kernel_project(project=project, family=request.data.get('family'))
        except KernelPropagationError as kpe:
            return Response(
                data={'description': str(kpe)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return self.retrieve(request, pk, *args, **kwargs)


class XFormViewSet(MtViewSetMixin, viewsets.ModelViewSet):
    '''
    Create new xForms entries providing:

    - the XLS Form definition or
    - the XML Data (via file or raw data)

    '''

    queryset = XForm.objects \
                    .prefetch_related('media_files') \
                    .order_by('title')
    serializer_class = XFormSerializer
    search_fields = ('title', 'description', 'xml_data',)
    mt_field = 'project'

    def get_queryset(self):
        queryset = super(XFormViewSet, self).get_queryset()

        project_id = self.request.query_params.get('project_id', None)
        if project_id is not None:
            queryset = queryset.filter(project=project_id)

        return queryset

    @action(detail=True, methods=['patch'])
    def propagate(self, request, pk=None, *args, **kwargs):
        '''
        Creates the artefacts of the xform in Aether Kernel server.

        Reachable at ``.../xforms/{pk}/propagate/``
        '''

        xform = self.get_object_or_404(pk=pk)
        xform.save()  # creates avro schema if missing

        try:
            propagate_kernel_artefacts(xform=xform, family=request.data.get('family'))
        except KernelPropagationError as kpe:
            return Response(
                data={'description': str(kpe)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return self.retrieve(request, pk, *args, **kwargs)


class MediaFileViewSet(MtViewSetMixin, viewsets.ModelViewSet):
    '''
    Create new Media File entries.
    '''

    queryset = MediaFile.objects.order_by('name')
    serializer_class = MediaFileSerializer
    search_fields = ('name', 'xform__title',)
    mt_field = 'xform__project'


class SurveyorViewSet(MtUserViewSetMixin, viewsets.ModelViewSet):
    '''
    Create new Surveyors entries providing:

    - Username
    - Password

    '''

    queryset = get_surveyors()
    serializer_class = SurveyorSerializer
    search_fields = ('username',)

    def get_queryset(self):
        queryset = super(SurveyorViewSet, self).get_queryset()

        project_id = self.request.query_params.get('project_id', None)
        if project_id is not None:
            # get forms with this project id and with surveyors
            xforms = XForm.objects \
                          .filter(project=project_id) \
                          .exclude(surveyors=None) \
                          .values_list('surveyors', flat=True)

            # take also the Project surveyors
            projects = Project.objects \
                              .filter(project_id=project_id) \
                              .exclude(surveyors=None) \
                              .values_list('surveyors', flat=True)

            items = xforms.union(projects)
            # build the surveyors list
            surveyors = set([])
            for item in items:
                try:
                    surveyors = surveyors.union(item)
                except Exception:
                    surveyors.add(item)
            # filter by these surveyors
            queryset = queryset.filter(id__in=surveyors)

        return queryset
