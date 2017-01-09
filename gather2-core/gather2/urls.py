from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin

from core import views

from .routers import TemplateRouter

router = TemplateRouter(template_name='index.html')

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
    router.register('map-functions', views.MapFunctionViewSet,
                    base_name='map_function')
    .register('map-results', views.MapResultViewSet,
              base_name='map_function_result',
              parents_query_lookups=['map_function'])
)

(
    router.register('map-functions', views.MapFunctionViewSet,
                    base_name='map_function')
    .register('reduce-functions', views.ReduceFunctionViewSet,
              base_name='map_reduce_function',
              parents_query_lookups=['map_function'])
)

router.register('map-results', views.MapResultViewSet, base_name='map_results')
router.register('reduce-functions', views.ReduceFunctionViewSet,
                base_name='reduce_function')
router.register('responses', views.ResponseViewSet, base_name='response')
router.register('attachments', views.AttachmentViewSet, base_name='attachment')


urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),
    url(r'', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
    url(r'^admin/', include(admin.site.urls))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
