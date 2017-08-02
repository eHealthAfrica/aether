import re
import requests
import xmltodict

from dateutil import parser
from django.shortcuts import get_object_or_404
from geojson import Point

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

from .core_utils import get_auth_header
from .models import XForm
from .serializers import XFormSerializer

from importer.settings import logger


class XFormViewset(viewsets.ModelViewSet):
    queryset = XForm.objects.all()
    serializer_class = XFormSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def form_list(request):
    xforms = XForm.objects.all()
    context = {
        'xforms': xforms,
        'host': request.build_absolute_uri().replace(request.get_full_path(), '')
    }
    headers = {
        'X-OpenRosa-Version': '1.0'
    }
    return Response(context,
                    template_name='xformsList.xml',
                    content_type='text/xml',
                    headers=headers)


@api_view(['GET'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def download_xform(request, pk):
    xform = get_object_or_404(XForm, pk=pk)
    return Response(xform.xml_data, content_type='text/xml')


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_manifest(request, id_string):
    # TODO ???
    context = {}
    headers = {
        'X-OpenRosa-Version': '1.0'
    }
    return Response(context,
                    template_name='xformsManifest.xml',
                    content_type='text/xml',
                    headers=headers)


@api_view(['POST', 'HEAD'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def submission(request):
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
        return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

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
    xform = XForm.objects.filter(form_id=form_id).first()
    if not xform:
        logger.error('xForm entry {} not found.'.format(form_id))
        return Response(status=status.HTTP_404_NOT_FOUND)

    coerce_dict = {}
    # bind entries define the fields and its types or possible values (choices list)
    for bind_entry in re.findall(r'<bind.*/>', xform.xml_data):
        re_nodeset = re.findall(r'nodeset="([^"]*)"', bind_entry)
        re_type = re.findall(r'type="([^"]*)"', bind_entry)

        try:
            coerce_dict[re_nodeset[0]] = re_type[0]
        except:
            # ignore, sometimes there is no "type"
            # <bind nodeset="/None/some_field" relevant=" /None/some_choice ='value'"/>
            pass

    walk(data, None, coerce_dict)  # modifies inplace

    try:
        response = requests.post(
            xform.gather_core_url,
            json={'data': data},
            headers=auth_header,
        )
        if response.status_code != 201:
            logger.warning(
                'Unexpected response {} from Gather2 Core server when submiting form "{}"'.format(
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
            'Unexpected error from Gather2 Core server when submiting form "{}"'.format(form_id)
        )
        logger.error(str(e))
        # something went wrong... just send an 400 error
        return Response(status=status.HTTP_400_BAD_REQUEST)
