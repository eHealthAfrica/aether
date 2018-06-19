from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('pipelines', views.PipelineViewSet)

urlpatterns = router.urls
