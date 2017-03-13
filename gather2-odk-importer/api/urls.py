from django.conf.urls import url
from rest_framework import routers

from api import views


router = routers.DefaultRouter()
router.register(r'xforms', views.XFormViewset)
urlpatterns = router.urls

urlpatterns += [
    url(r'^formList$', views.form_list, name='form_list'),
    url(r'^forms/(?P<pk>[^/]+)/form\.xml$',
        views.download_xform, name='download_xform'),
    url(r'^xformsManifest/(?P<id_string>[^$]+)$',
        views.xform_manifest, name='xform_manifest'),
    url(r'^submission$', views.submission, name='submission'),
]
