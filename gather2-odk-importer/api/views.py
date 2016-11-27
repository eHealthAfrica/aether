from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, StaticHTMLRenderer
from rest_framework.decorators import api_view, renderer_classes, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import xmltodict
from .models import XForm


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
    print(context)
    headers = {
        'X-OpenRosa-Version': '1.0'
    }
    return Response(context, template_name='xformsList.xml', content_type='text/xml', headers=headers)


@api_view(['GET'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def download_xform(request, pk):
    xform = XForm.objects.get(pk=pk, username=request.user.username)
    print(xform)
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


@api_view(['POST'])
@renderer_classes([StaticHTMLRenderer])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def submission(request):
    xml = request.POST['xml_submission_file'].read()
    d = xmltodict.parse(xml)
    title = list(d.keys())[0]  # TODO: Make this better
    xform = XForm.objects.get(title=title)  # TODO: Make this better
    print(xform.gather_core_url)

    1 / 0
    return Response(status=status.HTTP_201_CREATED)
