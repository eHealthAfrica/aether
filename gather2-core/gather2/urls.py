"""gather2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, include

from core import views
from .routers import TemplateRouter
from django.contrib import admin


router = TemplateRouter(template_name='index.html')

(
    router.register('surveys', views.SurveyViewSet)
    .register('responses', views.ResponseViewSet,
              base_name='survey_response',
              parents_query_lookups=['survey'])
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


urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),
    url(r'', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^health/', views.AWSHealthView.as_view(), name='aws-health-view'),
]
