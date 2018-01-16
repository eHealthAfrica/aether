from rest_framework_extensions.routers import DefaultRouter
from . import views


router = DefaultRouter()

router.register('projects', views.ProjectViewSet, base_name='project')
router.register('mappings', views.MappingViewSet, base_name='mapping')
router.register('projectschemas', views.ProjectSchemaViewSet, base_name='projectschema')
router.register('submissions', views.SubmissionViewSet, base_name='submission')
router.register('attachments', views.AttachmentViewSet, base_name='attachment')
router.register('entities', views.EntityViewSet, base_name='entity')
router.register('schemas', views.SchemaViewSet, base_name='schema')

urlpatterns = router.urls
