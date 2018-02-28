from django.conf import settings


def gather_context(request):
    navigation_list = ['surveys', ]
    if settings.AETHER_ODK:
        navigation_list.append('surveyors')

    context = {
        'dev_mode': settings.DEBUG,
        'app_name': settings.APP_NAME,
        'navigation_list': navigation_list,
        'kernel_url': settings.AETHER_APPS['kernel']['url'],
    }

    if settings.AETHER_ODK:  # pragma: no cover
        context['odk_url'] = settings.AETHER_APPS['odk']['url']

    return context
