from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin


def current_datetime(request):  # pragma: no cover
    ''' simple view to return current datetime '''
    from django.http import HttpResponse
    from datetime import datetime

    return HttpResponse(datetime.now())


auth_urls = 'rest_framework.urls'
if settings.CAS_SERVER_URL:  # pragma: no cover
    import django_cas_ng.views

    auth_urls = [
        url(r'^login/$', django_cas_ng.views.login, name='login'),
        url(r'^logout/$', django_cas_ng.views.logout, name='logout'),
    ]


urlpatterns = [
    url(r'^$', current_datetime, name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rq/', include('django_rq.urls')),
    url(r'^sync/', include('api.urls', 'sync')),
    url(r'^accounts/', include(auth_urls, namespace='rest_framework')),
]
