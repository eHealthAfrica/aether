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

'''
Views needed by ODK Collect

https://docs.opendatakit.org/
'''

import logging
import json
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext as _

from rest_framework import status
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

from aether.sdk.multitenancy.utils import add_instance_realm_in_headers
from aether.sdk.utils import request as exec_request

from .models import XForm, MediaFile
from .kernel_utils import (
    check_kernel_connection,
    get_attachments_url,
    get_kernel_auth_header,
    get_submissions_url,
    propagate_kernel_artefacts,
    KernelPropagationError,
)
from .surveyors_utils import is_surveyor
from .xform_utils import get_instance_data_from_xml, parse_submission


OPEN_ROSA_HEADERS = {'X-OpenRosa-Version': '1.0'}

NATURE_SUBMIT_SUCCESS = 'submit_success'
NATURE_SUBMIT_ERROR = 'submit_error'

'''
ODK Collect sends the Survey responses within an attachment file in XML format.

Parameter name of the submission file:
'''
XML_SUBMISSION_PARAM = 'xml_submission_file'


# list of messages that can be translated
MSG_XFORM_VERSION_WARNING = _(
    'Requesting {requested_version} xform version, '
    'while current is {current_version}.'
)
MSG_KERNEL_CONNECTION_ERR = _(
    'Connection with Aether Kernel is not possible.'
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
    'xForm entry "{form_id}" unauthorized.'
)
MSG_SUBMISSION_XFORM_NOT_FOUND_ERR = _(
    'xForm entry "{form_id}" no found.'
)
MSG_SUBMISSION_XFORM_VERSION_WARNING = _(
    'Sending response to {submission_version} version of the xForm "{form_id}", '
    'while current is {current_version}.'
)
MSG_SUBMISSION_KERNEL_ARTEFACTS_ERR = _(
    'Unexpected error from Aether Kernel '
    'while checking the xForm artefacts "{form_id}".'
)
MSG_SUBMISSION_KERNEL_EXISTENT_INSTANCE_ID = _(
    'There is already a submission "{id}" in Aether Kernel with instance ID "{instance}".'
)
MSG_SUBMISSION_KERNEL_SUBMIT_ERR = _(
    'Unexpected response {status} from Aether Kernel '
    'while submitting data of the xForm "{form_id}".'
)
MSG_SUBMISSION_KERNEL_SUBMIT_ATTACHMENT_ERR = _(
    'Unexpected response {status} from Aether Kernel '
    'while submitting attachment of the xForm "{form_id}".'
)
MSG_SUBMISSION_SUBMIT_ERR = _(
    'Unexpected error from Aether Kernel '
    'while submitting data of the xForm "{form_id}".'
)
MSG_SUBMISSION_SUBMIT_SUCCESS = _(
    'Successfully submitted data of the xForm "{form_id}" to Aether Kernel.'
)
MSG_SUBMISSION_SUBMIT_SUCCESS_ID = _(
    'The submission with instance ID "{instance}" has ID "{id}" in Aether Kernel.'
)


logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_list(request, *args, **kwargs):
    '''
    https://docs.opendatakit.org/openrosa-form-list/

    '''

    xforms = XForm.objects.all()
    formID = request.query_params.get('formID')
    if formID:
        xforms = xforms.filter(form_id=formID)

    host = request.build_absolute_uri(request.path).replace(reverse('xform-list-xml'), '')
    # If the request is not HTTPS, the host must include port 8443
    # or ODK Collect will not be able to get the resource
    url_info = urlparse(host)
    if url_info.scheme != 'https' and not url_info.port:
        host = f'http://{url_info.netloc}:8443{url_info.path}'
    return Response(
        data={
            'xforms': [xf for xf in xforms if is_surveyor(request, xf)],
            'host': host,
            'verbose': request.query_params.get('verbose', '').lower() == 'true',
        },
        template_name='xformList.xml',
        content_type='text/xml',
        headers=OPEN_ROSA_HEADERS,
    )


@api_view(['GET'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_get_download(request, pk, *args, **kwargs):
    '''
    https://docs.opendatakit.org/openrosa-form-list/

    Represents the `<downloadUrl/>` entry in the forms list.

    '''

    xform = get_object_or_404(XForm, pk=pk)
    if not is_surveyor(request, xform):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    version = request.query_params.get('version', '0')
    # check provided version with current one
    if version < xform.version:
        logger.warning(MSG_XFORM_VERSION_WARNING.format(
            requested_version=version, current_version=xform.version))

    return Response(
        data=xform.xml_data,
        content_type='text/xml',
        headers=OPEN_ROSA_HEADERS,
    )


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def media_file_get_content(request, pk, *args, **kwargs):
    '''
    Returns the `<downloadUrl/>` content in the form manifest file.

    '''

    media = get_object_or_404(MediaFile, pk=pk)
    if not is_surveyor(request, media.xform):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    # get content from File Storage and return it back
    response = exec_request(method='GET', url=media.media_file_url)
    http_response = HttpResponse(
        content=response,
        status=response.status_code,
        content_type=response.headers.get('Content-Type'),
    )
    http_response['Content-Type'] = response.headers.get('Content-Type')
    # include "content-disposition" as header (required by ODK Collect)
    http_response['Content-Disposition'] = f'attachment; filename="{media.name}"'

    return http_response


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_get_manifest(request, pk, *args, **kwargs):
    '''
    https://docs.opendatakit.org/openrosa-form-list/

    Represents the `<manifestUrl/>` entry in the forms list.

    '''

    xform = get_object_or_404(XForm, pk=pk)
    if not is_surveyor(request, xform):
        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={'media_files': []},
            template_name='xformManifest.xml',
            content_type='text/xml',
            headers=OPEN_ROSA_HEADERS,
        )

    version = request.query_params.get('version', '0')
    # check provided version with current one
    if version < xform.version:
        logger.warning(MSG_XFORM_VERSION_WARNING.format(
            requested_version=version, current_version=xform.version))

    host = request.build_absolute_uri(request.path) \
                  .replace(reverse('xform-get-manifest', kwargs={'pk': pk}), '')
    # If the request is not HTTPS, the host must include port 8443
    # or ODK Collect will not be able to get the resource
    url_info = urlparse(host)
    if url_info.scheme != 'https' and not url_info.port:
        host = f'http://{url_info.netloc}:8443{url_info.path}'
    return Response(
        data={
            'host': host,
            'media_files': xform.media_files.all(),
        },
        template_name='xformManifest.xml',
        content_type='text/xml',
        headers=OPEN_ROSA_HEADERS,
    )


@api_view(['POST', 'HEAD'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_submission(request, *args, **kwargs):
    '''
    Submission specification:
    https://docs.opendatakit.org/openrosa-form-submission/

    Response specification:
    https://docs.opendatakit.org/openrosa-http/#openrosa-responses

    Any time a request is received the following steps are executed:

    1. Checks if the connection with Aether Kernel is possible.
       Otherwise responds with a 424 (failed dependency) status code.

    2. Checks if the request includes content as a FILE
       in the ``xml_submission_file`` param.
       Otherwise responds with a 422 (unprocessable entity) status code.

    3. Reads and parses the file content (from XML to JSON format).
       If fails responds with a 422 (unprocessable entity) status code.

    4. Checks if the content has a `meta.instanceID` value.
       This check is part of the OpenRosa spec.
       Otherwise responds with a 422 (unprocessable entity) status code.

    5. Checks if the xForm linked to the request exists in Aether ODK.
       Otherwise responds with a 404 (not found) status code.

    6. Checks if the request user is a granted surveyor of the xForm.
       Otherwise responds with a 401 (unauthorized) status code.

    7. Compares the content xForm version with the current xForm version.
       Warns if the content one is older than the current one and continues.

    8. Propagates xForm artefacts to Aether Kernel.
       (This creates all the required artefacts in Aether Kernel
       that receive the request content and extract the linked entities)
       If fails responds with a 424 (failed dependency) status code.

    Note: Any error beyond this point will respond with a 400 (bad request) status code.
          Also it will delete any submission or attachment linked to this request
          in Aether Kernel.

    9. Checks if the request instance ID is already in any Aether Kernel submission.
       As part of the OpenRosa specs, submissions with big attachments could be
       split in several requests depending on the size of the attachments.
       In all of the cases the ``xml_submission_file`` FILE is included in the
       request.

    9.1. If there is no submission in Aether Kernel with this instance ID,
         submits the parsed JSON content to Aether Kernel.
         Also submits the original XML content as an attachment of the submission.

    9.2. If there is at least one submission (there should be only one)
         warns about it and continues.

    10. Checks if there are more FILE entries in the request.

    10.1. If there are more files submits them as attachments linked to
          this submission to Aether Kernel.

    11. Responds with a 201 (created) status code.
    '''

    def _rollback_submission(submission_id):
        # delete submission and ignore response
        if submission_id:
            exec_request(
                method='delete',
                url=get_submissions_url(submission_id),
                headers=auth_header,
            )

    def _respond(nature, message, status):
        return Response(
            data={'nature': nature, 'message': message},
            status=status,
            template_name='openRosaResponse.xml',
            content_type='text/xml',
            headers=OPEN_ROSA_HEADERS,
        )

    # first of all check if the connection is possible
    if not check_kernel_connection():
        return _respond(
            nature=NATURE_SUBMIT_ERROR,
            message=MSG_KERNEL_CONNECTION_ERR,
            status=status.HTTP_424_FAILED_DEPENDENCY,
        )

    if request.method == 'HEAD':
        response = HttpResponse(status=status.HTTP_204_NO_CONTENT)
        for k, v in OPEN_ROSA_HEADERS.items():
            response[k] = v
        return response

    if not request.FILES or XML_SUBMISSION_PARAM not in request.FILES:
        # missing submitted data
        msg = MSG_SUBMISSION_MISSING_DATA_ERR
        logger.warning(msg)
        return _respond(
            nature=NATURE_SUBMIT_ERROR,
            message=msg,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        xml = request.FILES[XML_SUBMISSION_PARAM]
        xml_content = xml.read()  # the content will be sent as an attachment
        data, form_id, version, instance_id = get_instance_data_from_xml(xml_content)
    except Exception as e:
        msg = MSG_SUBMISSION_FILE_ERR
        logger.warning(msg)
        logger.error(str(e))
        return _respond(
            nature=NATURE_SUBMIT_ERROR,
            message=msg + '\n' + str(e),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

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
        return _respond(
            nature=NATURE_SUBMIT_ERROR,
            message=msg,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # take the first xForm in which the current user is granted surveyor
    # TODO take the one that matches the version
    xform = None
    xforms = False
    for xf in XForm.objects.filter(form_id=form_id).order_by('-version'):
        xforms = True
        if is_surveyor(request, xf):
            xform = xf
            break
    if not xform:
        if xforms:
            msg = MSG_SUBMISSION_XFORM_UNAUTHORIZED_ERR.format(form_id=form_id)
            logger.error(msg)
            return _respond(
                nature=NATURE_SUBMIT_ERROR,
                message=msg,
                status=status.HTTP_401_UNAUTHORIZED,
            )
        else:
            msg = MSG_SUBMISSION_XFORM_NOT_FOUND_ERR.format(form_id=form_id)
            logger.error(msg)
            return _respond(
                nature=NATURE_SUBMIT_ERROR,
                message=msg,
                status=status.HTTP_404_NOT_FOUND,
            )

    # check sent version with current one
    if version < xform.version:  # pragma: no cover
        logger.warning(MSG_SUBMISSION_XFORM_VERSION_WARNING.format(
            submission_version=version,
            current_version=xform.version,
            form_id=form_id,
        ))

    # make sure that the xForm artefacts already exist in Aether Kernel
    try:
        propagate_kernel_artefacts(xform)
    except KernelPropagationError as kpe:
        msg = MSG_SUBMISSION_KERNEL_ARTEFACTS_ERR.format(form_id=form_id)
        logger.warning(msg)
        logger.error(str(kpe))
        return _respond(
            nature=NATURE_SUBMIT_ERROR,
            message=msg + '\n' + str(kpe),
            status=status.HTTP_424_FAILED_DEPENDENCY,
        )

    data = parse_submission(data, xform.xml_data)
    submissions_url = get_submissions_url()
    auth_header = add_instance_realm_in_headers(xform, get_kernel_auth_header())

    try:
        submission_id = None
        previous_submissions_response = exec_request(
            method='get',
            url=submissions_url,
            headers=auth_header,
            params={'payload__meta__instanceID': instance_id},
        )
        previous_submissions = json.loads(previous_submissions_response.content.decode('utf-8'))
        previous_submissions_count = previous_submissions['count']

        # If there are no previous submissions with the same instance id as
        # the current submission, post this submission and assign its id to
        # `submission_id`.
        if previous_submissions_count == 0:
            submission_id = None
            response = exec_request(
                method='post',
                url=submissions_url,
                json={'payload': data, 'mappingset': str(xform.kernel_id)},
                headers=auth_header,
            )
            submission_content = response.content.decode('utf-8')

            if response.status_code != status.HTTP_201_CREATED:
                msg = MSG_SUBMISSION_KERNEL_SUBMIT_ERR.format(status=response.status_code, form_id=form_id)
                logger.warning(msg)
                logger.warning(submission_content)
                return _respond(
                    nature=NATURE_SUBMIT_ERROR,
                    message=msg + '\n' + submission_content,
                    status=response.status_code,
                )
            # If there is one field with non ascii characters, the usual
            # response.json() will throw a `UnicodeDecodeError`.
            submission_id = json.loads(submission_content).get('id')

        # If there already exists a submission with for this instance id, we
        # need to retrieve its submission id in order to be able to associate
        # attachments with it.
        else:
            submission_id = previous_submissions['results'][0]['id']

            msg = MSG_SUBMISSION_KERNEL_EXISTENT_INSTANCE_ID.format(instance=instance_id, id=submission_id)
            logger.warning(msg)
            logger.warning(previous_submissions['results'][0])

        # Submit attachments (if any) to the submission.
        attachments_url = get_attachments_url()
        for name, xf in request.FILES.items():
            # submit the XML file as an attachment but only for the first time
            if name != XML_SUBMISSION_PARAM or previous_submissions_count == 0:
                if name == XML_SUBMISSION_PARAM:
                    file_content = xml_content
                else:
                    file_content = xf

                response = exec_request(
                    method='post',
                    url=attachments_url,
                    data={'submission': submission_id},
                    files={'attachment_file': (xf.name, file_content, xf.content_type)},
                    headers=auth_header,
                )
                if response.status_code != status.HTTP_201_CREATED:
                    attachment_content = response.content.decode('utf-8')
                    msg = MSG_SUBMISSION_KERNEL_SUBMIT_ATTACHMENT_ERR.format(
                        status=response.status_code, form_id=form_id,
                    )
                    logger.warning(msg)
                    logger.warning(attachment_content)

                    # delete submission and return error
                    _rollback_submission(submission_id)

                    return _respond(
                        nature=NATURE_SUBMIT_ERROR,
                        message=msg + '\n' + attachment_content,
                        status=response.status_code,
                    )

        msg = MSG_SUBMISSION_SUBMIT_SUCCESS_ID.format(instance=instance_id, id=submission_id)
        logger.info(msg)

        return _respond(
            nature=NATURE_SUBMIT_SUCCESS,
            message=MSG_SUBMISSION_SUBMIT_SUCCESS.format(form_id=form_id),
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        msg = MSG_SUBMISSION_SUBMIT_ERR.format(form_id=form_id)
        logger.warning(msg)
        logger.error(str(e))

        # delete submission and ignore response
        _rollback_submission(submission_id)

        # something went wrong... just send an 400 error
        return _respond(
            nature=NATURE_SUBMIT_ERROR,
            message=msg + '\n' + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )
