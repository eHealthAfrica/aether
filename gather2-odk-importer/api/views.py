import re

import requests
from dateutil import parser
from django.shortcuts import get_object_or_404

import xmltodict
from geojson import Point
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (api_view, authentication_classes,
                                       permission_classes, renderer_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import StaticHTMLRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from .models import XForm


def walk(obj, parent_keys, coerce_dict):
    if not parent_keys:
        parent_keys = []

    for k, v in obj.items():
        keys = parent_keys + [k]
        if isinstance(v, dict):
            walk(v, keys, coerce_dict)
        elif isinstance(v, list):
            for i in v:
                # indicies are not important
                walk(i, keys, coerce_dict)
        else:
            xpath = '/' + '/'.join(keys)
            _type = coerce_dict.get(xpath)
            if _type == 'int':
                obj[k] = int(v)
            if _type == 'dateTime':
                obj[k] = parser.parse(v).isoformat()
            if _type == 'date':
                obj[k] = parser.parse(v).isoformat()
            if _type == 'geopoint':
                lat, lng, altitude, accuracy = v.split()
                obj[k] = Point((float(lat), float(lng)))


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def form_list(request):
    xforms = XForm.objects.filter(username=request.user.username)
    context = {
        'xforms': xforms,
        'host': request.build_absolute_uri().replace(
            request.get_full_path(), '')
    }
    headers = {
        'X-OpenRosa-Version': '1.0'
    }
    return Response(context, template_name='xformsList.xml', content_type='text/xml', headers=headers)


@api_view(['GET'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def download_xform(request, pk):
    xform = get_object_or_404(XForm, pk=pk, username=request.user.username)
    return Response(xform.xml_data, content_type='text/xml')


@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def xform_manifest(request, id_string):
    context = {}
    headers = {
        'X-OpenRosa-Version': '1.0'
    }
    return Response(context, template_name='xformsManifest.xml', content_type='text/xml', headers=headers)


@api_view(['POST', 'HEAD'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def submission(request):
    if request.method == 'POST':
        xml = request.FILES['xml_submission_file'].read()
        d = xmltodict.parse(xml)
        title = list(d.items())[0][1]['@id']
        xform = XForm.objects.get(title=title)
        coerce_dict = {}
        for n in re.findall(r"<bind.*/>", xform.xml_data):
            coerce_dict[re.findall(r'nodeset="([^"]*)"', n)
                        [0]] = re.findall(r'type="([^"]*)"', n)[0]
        walk(d, None, coerce_dict)  # modifies inplace
        r = requests.post(xform.gather_core_url, json={'data': d, 'survey': 1})
        return Response(status=r.status)
    return Response(status=status.HTTP_204_NO_CONTENT)
