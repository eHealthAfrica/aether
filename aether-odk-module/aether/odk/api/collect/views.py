# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

import datetime
import logging

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import StaticHTMLRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from aether.sdk.auth.utils import unparse_username
from aether.sdk.multitenancy.utils import (
    add_instance_realm_in_headers,
    filter_by_realm,
)
from aether.sdk.utils import request as exec_request

from ..models import XForm, MediaFile
from ..kernel_utils import (
    check_kernel_connection,
    get_attachments_url,
    get_kernel_auth_header,
    get_submissions_url,
    propagate_kernel_artefacts,
    KernelPropagationError,
)
from ..surveyors_utils import is_surveyor, is_granted_surveyor
from ..xform_utils import get_instance_data_from_xml, parse_submission
from .authentication import CollectAuthentication


OPEN_ROSA_HEADERS = {'X-OpenRosa-Version': '1.0'}

NATURE_FETCH_ERROR = 'fetch_error'
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
    'Unexpected response ({status}) from Aether Kernel '
    'while submitting data of the xForm "{form_id}".'
)
MSG_SUBMISSION_KERNEL_SUBMIT_ATTACHMENT_ERR = _(
    'Unexpected response ({status}) from Aether Kernel '
    'while submitting attachment "{name}" of the xForm "{form_id}".'
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
MSG_401_UNAUTHORIZED = _(
    'You do not have authorization to access this instance.'
)
MSG_INSTANCE_INACTIVE = _(
    'This xForm "{form_id}" is no longer active.'
)


logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


def _get_host(request, current_path):
    # ODK Collect needs the full URL to get the resources. They have only the path
    # like /my/resource/path/id but not the scheme or the host name,
    # using the current path we try to figure out the real host to build the
    # linked URLs in the XML templates.
    #
    # If our path is:               http://my-host:8080/my/nested/path/any-odk-url
    # and our current path is:      /any-odk-url
    # the result must be:           http://my-host:8080/my/nested/path

    return request.build_absolute_uri(request.path).replace(current_path, '')


def _get_instance(request, model, pk):
    '''
    Custom method that raises:

        - 404 NOTFOUND error if it does not exist

        - 401 UNAUTHORIZED error if the instance exists but
          is not accessible by current user (is surveyor)

    otherwise returns the instance
    '''

    instance = get_object_or_404(model, pk=pk)
    if not is_granted_surveyor(request, instance):
        raise AuthenticationFailed(detail=MSG_401_UNAUTHORIZED, code='authorization_failed')
    return instance


def _get_xforms(request):
    # returns the queryset of xforms filtered by current realm
    return filter_by_realm(request, XForm.objects.all(), 'project')


def _send_response(request, nature, message, status):
    xml_content = get_template(template_name='openRosaResponse.xml').render({
        'nature': nature,
        'message': message,
    })

    http_response = HttpResponse(
        content=xml_content,
        status=status,
        content_type='text/xml',
    )
    headers = {
        'User': request.user.username,
        'Date': str(now()),
        **OPEN_ROSA_HEADERS
    }
    for k, v in headers.items():
        http_response[k] = v
    return http_response


class IsAuthenticatedAndSurveyor(IsAuthenticated):
    '''
    Allows access only to surveyor users.
    '''

    def has_permission(self, request, view):
        return bool(
            super(IsAuthenticatedAndSurveyor, self).has_permission(request, view) and
            is_surveyor(request.user)
        )


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([CollectAuthentication])
@permission_classes([IsAuthenticatedAndSurveyor])
def xform_list(request, *args, **kwargs):
    '''
    https://docs.opendatakit.org/openrosa-form-list/

    '''

    xforms = _get_xforms(request).filter(project__active=True, active=True)
    formID = request.query_params.get('formID')
    if formID:
        xforms = xforms.filter(form_id=formID)

    return Response(
        data={
            'host': _get_host(request, reverse('xform-list-xml')),
            'xforms': [xf for xf in xforms if is_granted_surveyor(request, xf)],
            'verbose': request.query_params.get('verbose', '').lower() == 'true',
        },
        template_name='xformList.xml',
        content_type='text/xml',
        headers={
            'User': request.user.username,
            'Date': str(now()),
            **OPEN_ROSA_HEADERS
        },
    )


@api_view(['GET'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([CollectAuthentication])
@permission_classes([IsAuthenticatedAndSurveyor])
def xform_get_download(request, pk, *args, **kwargs):
    '''
    https://docs.opendatakit.org/openrosa-form-list/

    Represents the `<downloadUrl/>` entry in the forms list.

    '''

    xform = _get_instance(request, XForm, pk=pk)
    if not xform.is_active():
        return _send_response(
            request=request,
            nature=NATURE_FETCH_ERROR,
            message=MSG_INSTANCE_INACTIVE.format(form_id=xform.form_id),
            status=status.HTTP_404_NOT_FOUND,
        )

    version = request.query_params.get('version', '0')
    # check provided version with current one
    if version < xform.version:
        logger.warning(MSG_XFORM_VERSION_WARNING.format(
            requested_version=version, current_version=xform.version))

    return Response(
        data=xform.xml_data,
        content_type='text/xml',
        headers={
            'User': request.user.username,
            'Date': str(now()),
            **OPEN_ROSA_HEADERS
        },
    )


@api_view(['GET'])
@authentication_classes([CollectAuthentication])
@permission_classes([IsAuthenticatedAndSurveyor])
def media_file_get_content(request, pk, *args, **kwargs):
    '''
    Returns the `<downloadUrl/>` content in the form manifest file.

    '''

    media = _get_instance(request, MediaFile, pk=pk)
    if not media.is_active():
        return _send_response(
            request=request,
            nature=NATURE_FETCH_ERROR,
            message=MSG_INSTANCE_INACTIVE.format(form_id=media.xform.form_id),
            status=status.HTTP_404_NOT_FOUND,
        )
    return media.get_content(as_attachment=True)


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([CollectAuthentication])
@permission_classes([IsAuthenticatedAndSurveyor])
def xform_get_manifest(request, pk, *args, **kwargs):
    '''
    https://docs.opendatakit.org/openrosa-form-list/

    Represents the `<manifestUrl/>` entry in the forms list.

    '''

    xform = _get_instance(request, XForm, pk=pk)
    if not xform.is_active():
        return _send_response(
            request=request,
            nature=NATURE_FETCH_ERROR,
            message=MSG_INSTANCE_INACTIVE.format(form_id=xform.form_id),
            status=status.HTTP_404_NOT_FOUND,
        )

    version = request.query_params.get('version', '0')
    # check provided version with current one
    if version < xform.version:
        logger.warning(MSG_XFORM_VERSION_WARNING.format(
            requested_version=version, current_version=xform.version))

    return Response(
        data={
            'host': _get_host(request, reverse('xform-get-manifest', kwargs={'pk': pk})),
            'media_files': xform.media_files.all(),
        },
        template_name='xformManifest.xml',
        content_type='text/xml',
        headers={
            'User': request.user.username,
            'Date': str(now()),
            **OPEN_ROSA_HEADERS
        },
    )


@api_view(['POST', 'HEAD'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([CollectAuthentication])
@permission_classes([IsAuthenticatedAndSurveyor])
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

    5. Checks if the xForm linked to the request exists and is active in Aether ODK.
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
        # delete submission (with cascade parameter to delete linked entities too)
        # and ignore response
        if submission_id:
            exec_request(
                method='delete',
                url=get_submissions_url(submission_id),
                params={'cascade': 'true'},
                headers=auth_header,
            )

    # first of all check if the connection is possible
    if not check_kernel_connection():
        return _send_response(
            request=request,
            nature=NATURE_SUBMIT_ERROR,
            message=MSG_KERNEL_CONNECTION_ERR,
            status=status.HTTP_424_FAILED_DEPENDENCY,
        )

    if request.method == 'HEAD':
        head_response = HttpResponse(status=status.HTTP_204_NO_CONTENT)
        for k, v in OPEN_ROSA_HEADERS.items():
            head_response[k] = v
        head_response['Date'] = str(now())
        return head_response

    if not request.FILES or XML_SUBMISSION_PARAM not in request.FILES:
        # missing submitted data
        msg = MSG_SUBMISSION_MISSING_DATA_ERR
        logger.warning(msg)
        return _send_response(
            request=request,
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
        logger.debug(str(e))
        return _send_response(
            request=request,
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
        return _send_response(
            request=request,
            nature=NATURE_SUBMIT_ERROR,
            message=msg,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # check that there is at least one xForm with that id
    xforms = _get_xforms(request).filter(form_id=form_id)
    if not xforms.exists():
        msg = MSG_SUBMISSION_XFORM_NOT_FOUND_ERR.format(form_id=form_id)
        logger.debug(msg)
        return _send_response(
            request=request,
            nature=NATURE_SUBMIT_ERROR,
            message=msg,
            status=status.HTTP_404_NOT_FOUND,
        )
    # check that there is at least one active xForm instance
    xforms = xforms.filter(project__active=True, active=True)
    if not xforms.exists():
        msg = MSG_INSTANCE_INACTIVE.format(form_id=form_id)
        logger.debug(msg)
        return _send_response(
            request=request,
            nature=NATURE_SUBMIT_ERROR,
            message=msg,
            status=status.HTTP_404_NOT_FOUND,
        )

    # take the first xForm in which the current user is granted surveyor
    # TODO take the one that matches the version
    xform = None
    for xf in xforms.order_by('-version'):
        if is_granted_surveyor(request, xf):
            xform = xf
            break

    if not xform:
        msg = MSG_SUBMISSION_XFORM_UNAUTHORIZED_ERR.format(form_id=form_id)
        logger.debug(msg)
        return _send_response(
            request=request,
            nature=NATURE_SUBMIT_ERROR,
            message=msg,
            status=status.HTTP_401_UNAUTHORIZED,
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
        logger.debug(str(kpe))
        return _send_response(
            request=request,
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
            params={'fields': 'id', 'payload__meta__instanceID': instance_id},
        )
        previous_submissions = previous_submissions_response.json()
        previous_submissions_count = previous_submissions['count']

        # If there are no previous submissions with the same instance id as
        # the current submission, post this submission and assign its id to
        # `submission_id`.
        if previous_submissions_count == 0:
            # internal audit log
            data['_surveyor'] = unparse_username(request, request.user.username)
            data['_submitted_at'] = datetime.datetime.utcnow().isoformat()

            submission_response = exec_request(
                method='post',
                url=submissions_url,
                json={'payload': data, 'mappingset': str(xform.kernel_id)},
                headers=auth_header,
            )
            submission_content = submission_response.content.decode('utf-8')

            if submission_response.status_code != status.HTTP_201_CREATED:
                msg = MSG_SUBMISSION_KERNEL_SUBMIT_ERR.format(
                    status=submission_response.status_code, form_id=form_id,
                )
                logger.warning(msg)
                logger.warning(submission_content)
                return _send_response(
                    request=request,
                    nature=NATURE_SUBMIT_ERROR,
                    message=msg + '\n' + submission_content,
                    status=submission_response.status_code,
                )
            submission_id = submission_response.json()['id']

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

                attachment_response = exec_request(
                    method='post',
                    url=attachments_url,
                    data={'submission': submission_id},
                    files={'attachment_file': (xf.name, file_content, xf.content_type)},
                    headers=auth_header,
                )
                if attachment_response.status_code != status.HTTP_201_CREATED:
                    attachment_content = attachment_response.content.decode('utf-8')
                    msg = MSG_SUBMISSION_KERNEL_SUBMIT_ATTACHMENT_ERR.format(
                        status=attachment_response.status_code, form_id=form_id, name=name,
                    )
                    logger.warning(msg)
                    logger.warning(attachment_content)

                    # delete submission and return error
                    _rollback_submission(submission_id)

                    return _send_response(
                        request=request,
                        nature=NATURE_SUBMIT_ERROR,
                        message=msg + '\n' + attachment_content,
                        status=attachment_response.status_code,
                    )

        msg = MSG_SUBMISSION_SUBMIT_SUCCESS_ID.format(instance=instance_id, id=submission_id)
        logger.info(msg)

        return _send_response(
            request=request,
            nature=NATURE_SUBMIT_SUCCESS,
            message=MSG_SUBMISSION_SUBMIT_SUCCESS.format(form_id=form_id),
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        msg = MSG_SUBMISSION_SUBMIT_ERR.format(form_id=form_id)
        logger.warning(msg)
        logger.debug(str(e))

        # delete submission and ignore response
        _rollback_submission(submission_id)

        # something went wrong... just send an 400 error
        return _send_response(
            request=request,
            nature=NATURE_SUBMIT_ERROR,
            message=msg + '\n' + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )
