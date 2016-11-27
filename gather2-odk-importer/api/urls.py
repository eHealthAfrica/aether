from django.conf.urls import url

from api import views

urlpatterns = [
    url(r'^formList$', views.form_list, name='form_list'),
    url(r'^forms/(?P<pk>[^/]+)/form\.xml$',
        views.download_xform, name='download_xform'),
    url(r'^xformsManifest/(?P<id_string>[^$]+)$',
        views.xform_manifest, name='xform_manifest'),
    url(r'^submission$', views.submission, name='submission'),
]
