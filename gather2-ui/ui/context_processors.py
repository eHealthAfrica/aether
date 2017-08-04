from django.conf import settings


def gather2(request):
    return {
        'dev_mode': settings.DEBUG,
        'app_name': settings.APP_NAME,
    }
