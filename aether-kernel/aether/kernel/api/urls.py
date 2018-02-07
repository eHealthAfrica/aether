from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()

router.register('projects', views.ProjectViewSet)
router.register('mappings', views.MappingViewSet)
router.register('mappings-stats', views.MappingStatsViewSet, base_name='mappings_stats')
router.register('projectschemas', views.ProjectSchemaViewSet)
router.register('submissions', views.SubmissionViewSet)
router.register('attachments', views.AttachmentViewSet)
router.register('entities', views.EntityViewSet)
router.register('schemas', views.SchemaViewSet)

urlpatterns = router.urls + [
    url(r'^entity-extraction-test/$', views.test_entity_extraction, name='entity-extraction-test')
]
