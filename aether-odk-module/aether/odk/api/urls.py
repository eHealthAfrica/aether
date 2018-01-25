from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register('mappings', views.MappingViewSet)
router.register('xforms', views.XFormViewSet)
router.register('media-files', views.MediaFileViewSet)
router.register('surveyors', views.SurveyorViewSet)

urlpatterns = router.urls + [
    path('formList', views.xform_list, name='xform-list-xml'),
    path('forms/<slug:pk>/form.xml', views.xform_get_download, name='xform-get-download'),
    path('forms/<slug:pk>/manifest.xml', views.xform_get_manifest, name='xform-get-manifest'),
    path('submission', views.xform_submission, name='xform-submission'),
]
