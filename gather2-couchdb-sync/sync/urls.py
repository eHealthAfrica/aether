import django_cas_ng.views
from django.conf.urls import include, url
from django.contrib import admin


def current_datetime(request):  # pragma: no cover
    ''' simple view to return current datetime '''
    from django.http import HttpResponse
    from datetime import datetime

    return HttpResponse(datetime.now())


urlpatterns = [
    url(r'^$', current_datetime, name='index'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^rq/', include('django_rq.urls')),
    url(r'^sync/', include('api.urls', 'sync')),

    url(r'^accounts/login/$', django_cas_ng.views.login, name='cas_login'),
    url(r'^accounts/logout/$', django_cas_ng.views.logout, name='cas_logout'),
]
