from rest_framework import routers

from aether.common.conf.urls import url_pattern

from . import views


router = routers.DefaultRouter()
router.register(r'mappings', views.MappingViewSet)
router.register(r'xforms', views.XFormViewSet)
router.register(r'media-files', views.MediaFileViewSet)
router.register(r'surveyors', views.SurveyorViewSet)

urlpatterns = router.urls + [
    url_pattern(r'^formList$',
                views.xform_list,
                name='xform-list-xml'),
    url_pattern(r'^forms/(?P<pk>[^/]+)/form\.xml$',
                views.xform_get_download,
                name='xform-get-download'),
    url_pattern(r'^forms/(?P<pk>[^/]+)/manifest\.xml$',
                views.xform_get_manifest,
                name='xform-get-manifest'),
    url_pattern(r'^submission$',
                views.xform_submission,
                name='xform-submission'),
]
