from django.conf.urls import include, url

from .views import XFormViewSet

from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'formList', XFormViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
