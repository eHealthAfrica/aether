from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register('mappings', views.MappingViewSet)
router.register('xforms', views.XFormViewSet)
router.register('media-files', views.MediaFileViewSet)
router.register('surveyors', views.SurveyorViewSet)

urlpatterns = router.urls + [
    url(r'^formList$', views.xform_list, name='xform-list-xml'),
    url(r'^forms/(?P<pk>[^/]+)/form.xml$', views.xform_get_download, name='xform-get-download'),
    url(r'^forms/(?P<pk>[^/]+)/manifest.xml$', views.xform_get_manifest, name='xform-get-manifest'),
    url(r'^submission$', views.xform_submission, name='xform-submission'),
]
