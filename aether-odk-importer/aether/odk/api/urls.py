from django.conf.urls import url
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'surveys', views.SurveyViewset)
router.register(r'xforms', views.XFormViewset)
router.register(r'surveyors', views.SurveyorViewSet)
urlpatterns = router.urls

urlpatterns += [
    url(r'^formList$', views.xform_list, name='xform-list-xml'),
    url(r'^forms/(?P<pk>[^/]+)/form\.xml$', views.xform_get, name='xform-get-xml_data'),
    url(r'^submission$', views.xform_submission, name='xform-submission'),
    url(r'^enketo/(?P<pk>[^/]+)$', views.enketo, name='enketo'),
]
