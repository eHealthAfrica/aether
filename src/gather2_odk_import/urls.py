from django.conf.urls import include, url

from .views import XFormListView
from .views import XFormViewSet

from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'forms', XFormViewSet)


urlpatterns = []

urlpatterns += [
    url(r'^', include(router.urls)),
    url(r'^all_forms/$', XFormListView.as_view()),
]
