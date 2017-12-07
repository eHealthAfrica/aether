from rest_framework_extensions.routers import ExtendedDefaultRouter
from . import views


router = ExtendedDefaultRouter()

(
    router.register('projects', views.ProjectViewSet)
          .register('projectschemas', views.ProjectSchemaViewSet,
                    base_name='project_projectschema',
                    parents_query_lookups=['project__name'])
)

(
    router.register('projects', views.ProjectViewSet)
          .register('mappings', views.MappingViewSet,
                    base_name='project_mapping',
                    parents_query_lookups=['project__name'])
)

(
    router.register('mappings', views.MappingViewSet)
          .register('submissions', views.SubmissionViewSet,
                    base_name='mapping_submission',
                    parents_query_lookups=['mapping'])
)
(
    router.register('submissions', views.SubmissionViewSet)
          .register('entities', views.EntityViewSet,
                    base_name='submission_entity',
                    parents_query_lookups=['submission'])
)
(
    router.register('schemas', views.SchemaViewSet)
          .register('projectschemas', views.ProjectSchemaViewSet,
                    base_name='schema_projectschema',
                    parents_query_lookups=['schema__name'])
)
(
    router.register('projectschemas', views.ProjectSchemaViewSet)
          .register('entities', views.EntityViewSet,
                    base_name='projectschema_entity',
                    parents_query_lookups=['projectschema__name'])
)
(
    router.register('entities', views.EntityViewSet)
)

urlpatterns = router.urls
