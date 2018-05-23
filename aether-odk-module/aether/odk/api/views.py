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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import requests

from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import StaticHTMLRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from aether.common.kernel.utils import (
    get_attachments_url,
    get_auth_header,
    get_submissions_url,
)
from ..settings import logger

from .models import Project, XForm, MediaFile
from .serializers import (
    ProjectSerializer,
    MediaFileSerializer,
    SurveyorSerializer,
    XFormSerializer,
)
from .surveyors_utils import get_surveyors
from .xform_utils import (
    get_instance_data_from_xml,
    get_instance_id,
    parse_submission,
)

'''
ODK Collect sends the Survey responses within an attachment file in XML format.

Parameter name of the submission file:
'''
XML_SUBMISSION_PARAM = 'xml_submission_file'


class ProjectViewSet(viewsets.ModelViewSet):
    '''
    Create new Project entries.
    '''

    queryset = Project.objects.order_by('name')
    serializer_class = ProjectSerializer
    search_fields = ('name',)


class XFormViewSet(viewsets.ModelViewSet):
    '''
    Create new xForms entries providing:

    - the XLS Form definition or
    - the XML Data (via file or raw data)

    '''

    queryset = XForm.objects.order_by('title')
    serializer_class = XFormSerializer
    search_fields = ('title', 'description', 'xml_data',)

    def get_queryset(self):
        queryset = self.queryset

        project_id = self.request.query_params.get('project_id', None)
        if project_id is not None:
            queryset = queryset.filter(project=project_id)

        return queryset


class MediaFileViewSet(viewsets.ModelViewSet):
    '''
    Create new Media File entries.
    '''

    queryset = MediaFile.objects.order_by('name')
    serializer_class = MediaFileSerializer
    search_fields = ('name', 'xform__title',)


class SurveyorViewSet(viewsets.ModelViewSet):
    '''
    Create new Surveyors entries providing:

    - Username
    - Password

    '''

    queryset = get_surveyors()
    serializer_class = SurveyorSerializer
    search_fields = ('username',)

    def get_queryset(self):
        queryset = self.queryset

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


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_list(request):
    '''
    https://bitbucket.org/javarosa/javarosa/wiki/FormListAPI

    '''

    xforms = XForm.objects.all()
    formID = request.query_params.get('formID')
    if formID:
        xforms = xforms.filter(form_id=formID)

    return Response(
        data={
            'xforms': [f for f in xforms if f.is_surveyor(request.user)],
            'host': request.build_absolute_uri().replace(request.get_full_path(), ''),
            'verbose': request.query_params.get('verbose', '').lower() == 'true',
        },
        template_name='xformList.xml',
        content_type='text/xml',
        headers={'X-OpenRosa-Version': '1.0'},
    )


@api_view(['GET'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_get_download(request, pk):
    '''
    https://bitbucket.org/javarosa/javarosa/wiki/FormListAPI

    Represents the `<downloadUrl/>` entry in the forms list.

    '''

    xform = get_object_or_404(XForm, pk=pk)
    if not xform.is_surveyor(request.user):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    version = request.query_params.get('version', '0')
    # check provided version with current one
    if version < xform.version:
        logger.warning(
            'Requesting {} xform version, current is {}'.format(version, xform.version)
        )

    return Response(
        data=xform.xml_data,
        content_type='text/xml',
        headers={'X-OpenRosa-Version': '1.0'},
    )


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_get_manifest(request, pk):
    '''
    https://bitbucket.org/javarosa/javarosa/wiki/FormListAPI

    Represents the `<manifestUrl/>` entry in the forms list.

    '''

    xform = get_object_or_404(XForm, pk=pk)
    if not xform.is_surveyor(request.user):
        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={'media_files': []},
            template_name='xformManifest.xml',
            content_type='text/xml',
            headers={'X-OpenRosa-Version': '1.0'},
        )

    version = request.query_params.get('version', '0')
    # check provided version with current one
    if version < xform.version:
        logger.warning(
            'Requesting {} xform version, current is {}'.format(version, xform.version)
        )

    return Response(
        data={
            'media_files': xform.media_files.all(),
            # use `/media-basic` entrypoint to use Basic Authentication not UMS or Django
            'host': request.build_absolute_uri().replace(
                request.get_full_path(), settings.MEDIA_BASIC_URL),
        },
        template_name='xformManifest.xml',
        content_type='text/xml',
        headers={'X-OpenRosa-Version': '1.0'},
    )


@api_view(['POST', 'HEAD'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_submission(request):
    '''
    https://bitbucket.org/javarosa/javarosa/wiki/FormSubmissionAPI

    '''

    # first of all check if the connection is possible
    auth_header = get_auth_header()
    if not auth_header:
        return Response(status=status.HTTP_424_FAILED_DEPENDENCY)

    if request.method == 'HEAD':
        return Response(status=status.HTTP_204_NO_CONTENT)

    if not request.FILES or XML_SUBMISSION_PARAM not in request.FILES:
        # missing submitted data
        logger.warning('Missing submitted data')
        return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    try:
        xml = request.FILES[XML_SUBMISSION_PARAM]
        xml_content = xml.read()  # the content will be sent as an attachment
        data, form_id, version = get_instance_data_from_xml(xml_content)
    except Exception as e:
        logger.warning('Unexpected error when handling file')
        logger.error(str(e))
        return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    # take the first xForm in which the current user is granted surveyor
    # TODO take the one that matches the version
    xform = None
    xforms = False
    for f in XForm.objects.filter(form_id=form_id):
        xforms = True
        if f.is_surveyor(request.user):
            xform = f
            break
    if not xform:
        if xforms:
            logger.error('xForm entry {} unauthorized.'.format(form_id))
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.error('xForm entry {} not found.'.format(form_id))
            return Response(status=status.HTTP_404_NOT_FOUND)

    # check sent version with current one
    if version < xform.version:  # pragma: no cover
        logger.warning(
            'Sending response to {} xform version, current is {}'.format(version, xform.version)
        )

    data = parse_submission(data, xform.xml_data)
    submissions_url = get_submissions_url()

    try:
        # When handling submissions containing multiple attachments, ODK
        # Collect will split the submission into multiple POST requests. Using
        # the instance id of the submission, we can assign the attached files
        # to the correct submission.
        #
        # The code in this block makes some assumptions:
        #   1. The submission has an instance id, accessible at `data['meta']['instanceID']`.
        #   2. The instance id is globally unique.
        #   3. The form data in the submission is identical for all
        #      POST requests with the same instance id.
        #
        # These assumptions match the OpenRosa spec linked to above.
        instance_id = get_instance_id(data)
        if not instance_id:
            logger.warning('Instance id is missing in submission')
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        previous_submissions_response = requests.get(
            submissions_url,
            headers=auth_header,
            params={'instanceID': instance_id},
        )
        previous_submissions = json.loads(previous_submissions_response.content.decode('utf-8'))
        previous_submissions_count = previous_submissions['count']
        # If there are no previous submissions with the same instance id as
        # the current submission, save this submission and assign its id to
        # `submission_id`.
        if previous_submissions_count == 0:
            submission_id = None
            response = requests.post(
                submissions_url,
                json={
                    'mapping': str(xform.kernel_id),
                    'payload': data,
                },
                headers=auth_header,
            )
            submission_content = response.content.decode('utf-8')

            if response.status_code != status.HTTP_201_CREATED:
                logger.warning(
                    'Unexpected response {} from Aether Kernel server when submitting data "{}"'.format(
                        response.status_code, form_id,
                    )
                )
                logger.warning(submission_content)
                return Response(status=response.status_code)
            # If there is one field with non ascii characters, the usual
            # response.json() will throw a `UnicodeDecodeError`.
            submission_id = json.loads(submission_content).get('id')
        # If there already exists a submission with for this instance id, we
        # need to retrieve its submission id in order to be able to associate
        # attachments with it.
        else:
            submission_id = previous_submissions['results'][0]['id']

        # Submit attachments (if any) to the submission.
        attachments_url = get_attachments_url()
        for name, f in request.FILES.items():
            # submit the XML file as an attachment but only for the first time
            if name != XML_SUBMISSION_PARAM or previous_submissions_count == 0:
                if name == XML_SUBMISSION_PARAM:
                    file_content = xml_content
                else:
                    file_content = f

                response = requests.post(
                    attachments_url,
                    data={'submission': submission_id},
                    files={'attachment_file': (f.name, file_content, f.content_type)},
                    headers=auth_header,
                )
                if response.status_code != status.HTTP_201_CREATED:
                    logger.warning(
                        'Unexpected response {} '
                        'from Aether Kernel server when submitting attachment "{}"'
                        .format(response.status_code, form_id))
                    logger.warning(response.content.decode('utf-8'))

                    # delete previous submission and return error
                    requests.delete(get_submissions_url(submission_id), headers=auth_header)
                    return Response(status=response.status_code)

        return Response(status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.warning(
            'Unexpected error from Aether Kernel server when submitting data "{}"'.format(form_id)
        )
        logger.error(str(e))

        if submission_id:
            # delete previous submission and ignore response
            requests.delete(get_submissions_url(submission_id), headers=auth_header)
        # something went wrong... just send an 400 error
        return Response(status=status.HTTP_400_BAD_REQUEST)
