
from django.conf import settings


def ui_context(request):

    context = {
        'dev_mode': settings.DEBUG,
        'app_name': settings.APP_NAME,
        'kernel_url': settings.AETHER_APPS['kernel']['url'],
    }

    return context
