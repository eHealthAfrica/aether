"""
gather2_couchdb_sync URL Configuration
"""
from django.conf.urls import include, url
from django.contrib import admin
# import django_cas_ng.views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rq/', include('django_rq.urls')),
    url(r'^sync/', include('api.urls', 'sync')),
    # url(r'^accounts/login/$', django_cas_ng.views.login, name="cas_login"),
    # url(r'^accounts/logout/$', django_cas_ng.views.logout, name="cas_logout"),
]
