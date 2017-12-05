from django.conf import settings


def aether(request):
    navigation_list = ['surveys', ]
    if settings.AETHER_ODK:
        navigation_list.append('surveyors')

    return {
        'dev_mode': settings.DEBUG,
        'app_name': settings.APP_NAME,
        'org_name': settings.ORG_NAME,
        'odk_active': settings.AETHER_ODK,
        'navigation_list': navigation_list,
    }
