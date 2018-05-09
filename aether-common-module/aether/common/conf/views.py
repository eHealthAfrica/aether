import os

from django.conf import settings
from django.http import HttpResponse

from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated


# Taken from: http://glitterbug.in/blog/serving-protected-files-from-nginx-with-django-11/show/
def media_serve(request, path, *args, **kwargs):  # pragma: no cover
    """
    Redirect the request to the path used by nginx for protected media.
    """

    response = HttpResponse(status=200, content_type='')
    response['X-Accel-Redirect'] = os.path.join(settings.MEDIA_INTERNAL_URL, path)
    return response


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def basic_serve(request, path, *args, **kwargs):  # pragma: no cover
    """
    Redirect the request to the path used by nginx for protected media using BASIC Authentication.
    """
    return media_serve(request, path, *args, **kwargs)
