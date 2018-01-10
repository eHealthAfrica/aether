from django.http import JsonResponse


def health(*args, **kwargs):
    '''
    Simple view to check if the system is up.
    '''

    return JsonResponse({})
