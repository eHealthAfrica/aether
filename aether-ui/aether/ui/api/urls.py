from rest_framework import routers
from django.conf.urls import url

from . import views

router = routers.DefaultRouter()
router.register('pipelines', views.PipelineViewSet)

urlpatterns = router.urls + [
  url(r'^kernel-url/$',
      views.get_kernel_url,
      name='kernel-url')
]
