from django.http import HttpResponse, JsonResponse
from .utils import check_connection


def check_kernel(*args, **kwargs):
    '''
    Check if the connection with Kernel server is possible
    '''

    return HttpResponse(check_connection())


def health_check(*args, **kwargs):
    return JsonResponse({})
