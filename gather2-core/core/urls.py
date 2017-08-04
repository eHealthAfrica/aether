from rest_framework_extensions.routers import ExtendedDefaultRouter
from . import views


router = ExtendedDefaultRouter()

(
    router.register('surveys', views.SurveyViewSet)
          .register('responses', views.ResponseViewSet,
                    base_name='survey_response',
                    parents_query_lookups=['survey'])
)

(
    router.register('responses', views.ResponseViewSet)
          .register('attachments', views.AttachmentViewSet,
                    base_name='response_attachment',
                    parents_query_lookups=['response'])
)

(
    router.register('surveys', views.SurveyViewSet)
          .register('map-functions', views.MapFunctionViewSet,
                    base_name='survey_map_function',
                    parents_query_lookups=['survey'])
)

(
    router.register('map-functions', views.MapFunctionViewSet, base_name='map_function')
          .register('map-results', views.MapResultViewSet,
                    base_name='map_function_result',
                    parents_query_lookups=['map_function'])
)

(
    router.register('map-functions', views.MapFunctionViewSet, base_name='map_function')
          .register('reduce-functions', views.ReduceFunctionViewSet,
                    base_name='map_reduce_function',
                    parents_query_lookups=['map_function'])
)

router.register('map-results', views.MapResultViewSet, base_name='map_results')
router.register('reduce-functions', views.ReduceFunctionViewSet, base_name='reduce_function')
router.register('responses', views.ResponseViewSet, base_name='response')
router.register('attachments', views.AttachmentViewSet, base_name='attachment')

urlpatterns = router.urls
