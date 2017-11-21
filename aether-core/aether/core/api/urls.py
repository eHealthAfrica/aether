from rest_framework_extensions.routers import ExtendedDefaultRouter
from . import views


router = ExtendedDefaultRouter()

(
    router.register('projects', views.ProjectViewSet)
          .register('projectschemas', views.ProjectSchemaViewSet,
                    base_name='project_projectschema',
                    parents_query_lookups=['project'])
)

(
    router.register('projects', views.ProjectViewSet)
          .register('mappings', views.MappingViewSet,
                    base_name='project_mapping',
                    parents_query_lookups=['project'])
)

(
    router.register('mappings', views.MappingViewSet)
          .register('responses', views.ResponseViewSet,
                    base_name='mapping_response',
                    parents_query_lookups=['mapping'])
)
(
    router.register('responses', views.ResponseViewSet)
          .register('entities', views.EntityViewSet,
                    base_name='response_entity',
                    parents_query_lookups=['response'])
)
(
    router.register('schemas', views.SchemaViewSet)
          .register('projectschemas', views.ProjectSchemaViewSet,
                    base_name='schema_projectschema',
                    parents_query_lookups=['schema'])
)
(
    router.register('projectschemas', views.ProjectSchemaViewSet)
          .register('entities', views.EntityViewSet,
                    base_name='projectschema_entity',
                    parents_query_lookups=['projectschema'])
)
(
    router.register('entities', views.EntityViewSet)
)

router.register('projects', views.ProjectViewSet, base_name='project')
router.register('mappings', views.MappingViewSet, base_name='mapping')
router.register('responses', views.ResponseViewSet, base_name='response')
router.register('schemas', views.SchemaViewSet, base_name='schema')
router.register('projectschemas', views.ProjectSchemaViewSet, base_name='projectschema')
router.register('entities', views.EntityViewSet, base_name='entity')

urlpatterns = router.urls
