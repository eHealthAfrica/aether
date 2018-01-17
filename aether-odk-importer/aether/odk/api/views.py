import re
import requests
import xmltodict

from dateutil import parser
from geojson import Point

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

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

from aether.common.kernel.utils import get_auth_header
from .models import Survey, XForm
from .serializers import SurveySerializer, XFormSerializer, SurveyorSerializer
from .surveyors_utils import get_surveyors

from ..settings import logger


class SurveyViewset(viewsets.ModelViewSet):
    '''
    Create new Survey entries.
    '''
    queryset = Survey.objects.order_by('name')
    serializer_class = SurveySerializer
    search_fields = ('name',)

    def partial_update(self, request, pk, *args, **kwargs):
        '''
        We are posting the xForms in only one call, to update them all together.

        There are two options:
        - JSON format
        - Multipart format

        The first case will be straight forward, the second one will imply FILES.
        This means that only a list with the form id and the file will be sent.
        The xforms will be created or updated with this info.
        '''

        instance = get_object_or_404(Survey, pk=pk)
        data = request.data

        if request.FILES or 'files' in data:
            return self.partial_update_with_files(request, instance)

        if 'xforms' not in data:
            return Response(
                data={'xforms': [_('This field is required')]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self.partial_update_without_files(request, instance, data['xforms'])

    @transaction.atomic
    def partial_update_with_files(self, request, survey):
        '''
        Updates or creates xForms with file content.

        Expected format:
        - `files`: number of files to upload
            For each # in length range:
                - `id_#`: xform id or 0 for new entries
                - `file_#`: file content
        '''
        for index in range(int(request.data['files'])):
            xform_id = int(request.data['id_' + str(index)])
            data = {
                'survey': survey.pk,
                'xml_file': request.data['file_' + str(index)],
            }

            if xform_id > 0:
                data['id'] = xform_id
                serializer = XFormSerializer(
                    XForm.objects.get(pk=xform_id),
                    data=data,
                    context={'request': request},
                )
            else:
                serializer = XFormSerializer(
                    data=data,
                    context={'request': request},
                )

            if serializer.is_valid():
                serializer.save()
            else:
                return Response(
                    data=serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            data=self.serializer_class(survey, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    @transaction.atomic
    def partial_update_without_files(self, request, survey, xforms):
        '''
        Every time that a Survey is partially updated all its xForms are also
        created, updated or even deleted if they are not longer in use.
        '''

        xform_ids = []
        for xform in xforms:
            xform['survey'] = survey.pk

            if 'id' in xform and xform['id']:
                serializer_xform = XFormSerializer(
                    XForm.objects.get(pk=xform['id']),
                    data=xform,
                    context={'request': request},
                )
            else:
                serializer_xform = XFormSerializer(data=xform, context={'request': request})

            if serializer_xform.is_valid():
                serializer_xform.save()
                xform_ids.append(serializer_xform.data['id'])
            else:
                return Response(
                    data=serializer_xform.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # remove orphans form survey
        XForm.objects \
             .filter(survey=survey) \
             .exclude(id__in=xform_ids) \
             .delete()

        return Response(
            data=self.serializer_class(survey, context={'request': request}).data,
            status=status.HTTP_200_OK
        )


class XFormViewset(viewsets.ModelViewSet):
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

        mapping_id = self.request.query_params.get('mapping_id', None)
        if mapping_id is not None:
            queryset = queryset.filter(survey=mapping_id)

        return queryset


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

        mapping_id = self.request.query_params.get('mapping_id', None)
        if mapping_id is not None:
            # get forms with this survey id and with surveyors
            xforms = XForm.objects \
                          .filter(survey=mapping_id) \
                          .exclude(surveyors=None) \
                          .values_list('surveyors', flat=True)

            # take also the Survey surveyors
            surveys = Survey.objects \
                            .filter(mapping_id=mapping_id) \
                            .exclude(surveyors=None) \
                            .values_list('surveyors', flat=True)

            items = xforms.union(surveys)
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

    return Response(
        {
            'xforms': [f for f in XForm.objects.all() if f.is_surveyor(request.user)],
            'host': request.build_absolute_uri().replace(request.get_full_path(), ''),
        },
        template_name='xformsList.xml',
        content_type='text/xml',
        headers={'X-OpenRosa-Version': '1.0'},
    )


@api_view(['GET'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_get(request, pk):
    '''
    https://bitbucket.org/javarosa/javarosa/wiki/FormListAPI

    Represents the `<downloadUrl/>` entry in the forms list.
    '''

    xform = get_object_or_404(XForm, pk=pk)
    if not xform.is_surveyor(request.user):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    return Response(xform.xml_data, content_type='text/xml')


@api_view(['POST', 'HEAD'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_submission(request):
    '''
    https://bitbucket.org/javarosa/javarosa/wiki/FormSubmissionAPI
    '''

    def walk(obj, parent_keys, coerce_dict):
        if not parent_keys:
            parent_keys = []

        for k, v in obj.items():
            keys = parent_keys + [k]
            if isinstance(v, dict):
                walk(v, keys, coerce_dict)
            elif isinstance(v, list):
                for i in v:
                    # indices are not important
                    walk(i, keys, coerce_dict)
            elif v is not None:
                xpath = '/' + '/'.join(keys)
                _type = coerce_dict.get(xpath)
                if _type in ('int', 'integer'):
                    obj[k] = int(v)
                if _type == 'decimal':
                    obj[k] = float(v)
                if _type in ('date', 'dateTime'):
                    obj[k] = parser.parse(v).isoformat()
                if _type == 'geopoint':
                    lat, lng, altitude, accuracy = v.split()
                    # {"coordinates": [<<lat>>, <<lng>>], "type": "Point"}
                    obj[k] = Point((float(lat), float(lng)))

    # first of all check if the connection is possible
    auth_header = get_auth_header()
    if not auth_header:
        return Response(status=status.HTTP_424_FAILED_DEPENDENCY)

    if request.method == 'HEAD':
        return Response(status=status.HTTP_204_NO_CONTENT)

    file_param = 'xml_submission_file'
    try:
        xml = request.FILES[file_param].read()
        data = xmltodict.parse(xml)
    except Exception as e:
        logger.warning('Unexpected error when handling file')
        logger.error(str(e))
        return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    form_id = list(data.items())[0][1]['@id']  # TODO make more robust

    # take the first xForm in which the current user is granted surveyor
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

    coerce_dict = {}
    # bind entries define the fields and its types or possible values (choices list)
    for bind_entry in re.findall(r'<bind.*/>', xform.xml_data):
        re_nodeset = re.findall(r'nodeset="([^"]*)"', bind_entry)
        re_type = re.findall(r'type="([^"]*)"', bind_entry)

        try:
            coerce_dict[re_nodeset[0]] = re_type[0]
        except Exception:
            # ignore, sometimes there is no "type"
            # <bind nodeset="/None/some_field" relevant=" /None/some_choice ='value'"/>
            pass

    walk(data, None, coerce_dict)  # modifies inplace
    try:
        response = requests.post(
            xform.aether_kernel_url,
            json={'payload': data},
            headers=auth_header,
        )
        if response.status_code != 201:
            logger.warning(
                'Unexpected response {} from Aether Kernel server when submiting form "{}"'.format(
                    response.status_code, form_id
                )
            )
            logger.warning(response.content.decode())
            return Response(status=response.status_code)

        attachment_url = response.json().get('attachments_url')

        for name, f in request.FILES.items():
            # submit possible attachments to the response and ignore response
            if name != file_param:
                requests.post(
                    attachment_url,
                    data={'name': name},
                    files={'attachment_file': (f.name, f, f.content_type)},
                    headers=auth_header,
                )

        return Response(status=response.status_code)

    except Exception as e:
        logger.warning(
            'Unexpected error from Aether Kernel server when submiting form "{}"'.format(form_id)
        )
        logger.error(str(e))
        # something went wrong... just send an 400 error
        return Response(status=status.HTTP_400_BAD_REQUEST)

import requests

@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
# @authentication_classes([BasicAuthentication])
def enketo(request):
    # TODO:
    # document enketo-core/enketo-transformer
    # add tests
    # add webpack to container entrypoint
    # ./node_modules/.bin/webpack --entry ./index.js --output-filename ../aether/odk/static/out.js
    # TODO: get xform and make request to transformer
    return Response(
        {
            'test': 123,
        },
        template_name='enketo.html',
        content_type='text/html',
    )
