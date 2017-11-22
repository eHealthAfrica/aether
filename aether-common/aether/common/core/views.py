from django.http import HttpResponse
from .utils import check_connection


def check_core(*args, **kwargs):
    '''
    Check if the connection with Core server is possible
    '''

    return HttpResponse(check_connection())
