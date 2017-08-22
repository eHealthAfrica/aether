from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin


def check_core(request):  # pragma: no cover
    '''
    Check if the connection with Core server is possible
    '''
    from api.core_utils import test_connection
    from django.http import HttpResponse

    if not test_connection():
        return HttpResponse('Always Look on the Bright Side of Life!!!')
    return HttpResponse('Brought to you by eHealth Africa - good tech for hard places')


auth_urls = 'rest_framework.urls'
if settings.CAS_SERVER_URL:  # pragma: no cover
    import django_cas_ng.views

    auth_urls = [
        url(r'^login/$', django_cas_ng.views.login, name='login'),
        url(r'^logout/$', django_cas_ng.views.logout, name='logout'),
    ]


urlpatterns = [
    url(r'^$', check_core, name='index'),
    url(r'^core$', check_core, name='check-core'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rq/', include('django_rq.urls')),
    url(r'^sync/', include('api.urls', 'sync')),
    url(r'^accounts/', include(auth_urls, namespace='rest_framework')),
]
