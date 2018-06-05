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

import json
import requests

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework import viewsets, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (
    action,
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
from .kernel_utils import (
    propagate_kernel_project,
    propagate_kernel_artefacts,
    KernelPropagationError,
)
from .surveyors_utils import get_surveyors
from .xform_utils import get_instance_data_from_xml, parse_submission


# list of messages that can be translated
MSG_XFORM_VERSION_WARNING = _(
    'Requesting {requested_version} xform version, current is {current_version}'
)
MSG_KERNEL_CONNECTION_ERR = _(
    'Connection with Aether Kernel server is not possible.'
)
MSG_SUBMISSION_MISSING_DATA_ERR = _(
    'Missing submitted data.'
)
MSG_SUBMISSION_FILE_ERR = _(
    'Unexpected error while handling submission file.'
)
MSG_SUBMISSION_MISSING_INSTANCE_ID_ERR = _(
    'Instance ID is missing in submission.'
)
MSG_SUBMISSION_XFORM_UNAUTHORIZED_ERR = _(
    'xForm entry {form_id} unauthorized.'
)
MSG_SUBMISSION_XFORM_NOT_FOUND_ERR = _(
    'xForm entry {form_id} no found.'
)
MSG_SUBMISSION_XFORM_VERSION_WARNING = _(
    'Sending response to {submission_version} xform version, current is {current_version}'
)
MSG_SUBMISSION_KERNEL_ARTEFACTS_ERR = _(
    'Unexpected error from Aether Kernel server '
    'while checking the xForm artefacts "{form_id}".'
)
MSG_SUBMISSION_KERNEL_SUBMIT_ERR = _(
    'Unexpected response {status} from Aether Kernel server '
    'while submitting data of the xForm "{form_id}".'
)
MSG_SUBMISSION_KERNEL_SUBMIT_ATTACHMENT_ERR = _(
    'Unexpected response {status} from Aether Kernel server '
    'while submitting attachment of the xForm "{form_id}".'
)
MSG_SUBMISSION_SUBMIT_ERR = _(
    'Unexpected error from Aether Kernel server '
    'while submitting data of the xForm "{form_id}".'
)


class ProjectViewSet(viewsets.ModelViewSet):
    '''
    Create new Project entries.
    '''

    queryset = Project.objects \
                      .prefetch_related('xforms', 'xforms__media_files') \
                      .order_by('name')
    serializer_class = ProjectSerializer
    search_fields = ('name',)

    @action(detail=True, methods=['patch'])
    def propagates(self, request, pk=None, *args, **kwargs):
        '''
        Creates a copy of the project in Aether Kernel server.

        Reachable at ``.../projects/{pk}/propagates/``
        '''

        project = get_object_or_404(Project, pk=pk)

        try:
            propagate_kernel_project(project)
        except KernelPropagationError as kpe:
            return Response(
                data={'description': str(kpe)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return self.retrieve(request, pk, *args, **kwargs)


class XFormViewSet(viewsets.ModelViewSet):
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

    def get_queryset(self):
        queryset = self.queryset

        project_id = self.request.query_params.get('project_id', None)
        if project_id is not None:
            queryset = queryset.filter(project=project_id)

        return queryset

    @action(detail=True, methods=['patch'])
    def propagates(self, request, pk=None, *args, **kwargs):
        '''
        Creates the artefacts of the xform in Aether Kernel server.

        Reachable at ``.../xforms/{pk}/propagates/``
        '''

        xform = get_object_or_404(XForm, pk=pk)
        xform.save()  # creates avro schema if missing

        try:
            propagate_kernel_artefacts(xform)
        except KernelPropagationError as kpe:
            return Response(
                data={'description': str(kpe)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return self.retrieve(request, pk, *args, **kwargs)


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


'''
Views needed by ODK Collect

https://bitbucket.org/javarosa
'''


'''
ODK Collect sends the Survey responses within an attachment file in XML format.

Parameter name of the submission file:
'''
XML_SUBMISSION_PARAM = 'xml_submission_file'


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
        logger.warning(MSG_XFORM_VERSION_WARNING.format(
            requested_version=version, current_version=xform.version))

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
        logger.warning(MSG_XFORM_VERSION_WARNING.format(
            requested_version=version, current_version=xform.version))

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
        return Response(
            data=MSG_KERNEL_CONNECTION_ERR,
            status=status.HTTP_424_FAILED_DEPENDENCY,
        )

    if request.method == 'HEAD':
        return Response(status=status.HTTP_204_NO_CONTENT)

    if not request.FILES or XML_SUBMISSION_PARAM not in request.FILES:
        # missing submitted data
        msg = MSG_SUBMISSION_MISSING_DATA_ERR
        logger.warning(msg)
        return Response(data=msg, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    try:
        xml = request.FILES[XML_SUBMISSION_PARAM]
        xml_content = xml.read()  # the content will be sent as an attachment
        data, form_id, version, instance_id = get_instance_data_from_xml(xml_content)
    except Exception as e:
        msg = MSG_SUBMISSION_FILE_ERR
        logger.warning(msg)
        logger.error(str(e))
        return Response(data=msg + '\n' + str(e), status=status.HTTP_422_UNPROCESSABLE_ENTITY)

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
    if not instance_id:
        msg = MSG_SUBMISSION_MISSING_INSTANCE_ID_ERR
        logger.warning(msg)
        return Response(data=msg, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

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
            msg = MSG_SUBMISSION_XFORM_UNAUTHORIZED_ERR.format(form_id=form_id)
            logger.error(msg)
            return Response(data=msg, status=status.HTTP_401_UNAUTHORIZED)
        else:
            msg = MSG_SUBMISSION_XFORM_NOT_FOUND_ERR.format(form_id=form_id)
            logger.error(msg)
            return Response(data=msg, status=status.HTTP_404_NOT_FOUND)

    # check sent version with current one
    if version < xform.version:  # pragma: no cover
        logger.warning(MSG_SUBMISSION_XFORM_VERSION_WARNING.format(
            submission_version=version, current_version=xform.version))

    # make sure that the xForm artefacts already exist in Aether Kernel
    try:
        propagate_kernel_artefacts(xform)
    except KernelPropagationError as kpe:
        msg = MSG_SUBMISSION_KERNEL_ARTEFACTS_ERR.format(form_id=form_id)
        logger.warning(msg)
        logger.error(str(kpe))
        return Response(data=msg + '\n' + str(kpe), status=status.HTTP_424_FAILED_DEPENDENCY)

    data = parse_submission(data, xform.xml_data)
    submissions_url = get_submissions_url()

    try:
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
                msg = MSG_SUBMISSION_KERNEL_SUBMIT_ERR.format(status=response.status_code, form_id=form_id)
                logger.warning(msg)
                logger.warning(submission_content)
                return Response(data=msg + '\n' + submission_content, status=response.status_code)
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
                    attachment_content = response.content.decode('utf-8')
                    msg = MSG_SUBMISSION_KERNEL_SUBMIT_ATTACHMENT_ERR.format(
                        status=response.status_code, form_id=form_id)
                    logger.warning(msg)
                    logger.warning(attachment_content)

                    # delete previous submission and return error
                    requests.delete(get_submissions_url(submission_id), headers=auth_header)
                    return Response(data=msg + '\n' + attachment_content, status=response.status_code)

        return Response(status=status.HTTP_201_CREATED)

    except Exception as e:
        msg = MSG_SUBMISSION_SUBMIT_ERR.format(form_id=form_id)
        logger.warning(msg)
        logger.error(str(e))

        if submission_id:
            # delete previous submission and ignore response
            requests.delete(get_submissions_url(submission_id), headers=auth_header)
        # something went wrong... just send an 400 error
        return Response(data=msg + '\n' + str(e), status=status.HTTP_400_BAD_REQUEST)
