import os
import requests
import json

from django.conf import settings
from django.http import HttpResponse

from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from aether.common.conf import settings as app_settings


# Taken from: http://glitterbug.in/blog/serving-protected-files-from-nginx-with-django-11/show/
def media_serve(request, path, *args, **kwargs):  # pragma: no cover
    '''
    Redirect the request to the path used by nginx for protected media.
    '''

    response = HttpResponse(status=200, content_type='')
    response['X-Accel-Redirect'] = os.path.join(settings.MEDIA_INTERNAL_URL, path)
    return response


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def basic_serve(request, path, *args, **kwargs):  # pragma: no cover
    '''
    Redirect the request to the path used by nginx for protected media using BASIC Authentication.
    '''

    return media_serve(request, path, *args, **kwargs)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def setup_kong_consumer(request, *args, **kwargs):
    '''
    Create kong oauth2 credentials for authenticated user
    '''
    url = 'http://' + app_settings.PROJECT_API_URL + ':8001/consumers/' + app_settings.KONG_CONSUMER + '/oauth2'
    app_registration_data = {
        'redirect_uri': request.POST.get('redirect_uri') or 'http://' + app_settings.PROJECT_API_URL,
        'name': request.POST.get('app_name') or 'aether-app'
    }
    jsonData = json.dumps(app_registration_data)
    results = HttpResponse('Check that kong server is reachable')
    try:
        results = requests.post(url, json=jsonData,
                                headers={'Content-Type': 'application/json', 'apikey': app_settings.KONG_APIKEY})
    except Exception as e:
        print(str(e))
    return HttpResponse(results)
