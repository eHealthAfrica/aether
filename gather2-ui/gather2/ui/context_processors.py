from django.conf import settings


def gather2(request):
    navigation_list = ['surveys', ]
    if settings.GATHER_ODK:
        navigation_list.append('surveyors')

    return {
        'dev_mode': settings.DEBUG,
        'app_name': settings.APP_NAME,
        'org_name': settings.ORG_NAME,
        'odk_active': settings.GATHER_ODK,
        'navigation_list': navigation_list,
    }
