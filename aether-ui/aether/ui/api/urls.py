from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required

from rest_framework import routers

from .decorators import tokens_required
from . import views

router = routers.DefaultRouter()

router.register('pipelines', views.PipelineViewSet)
router.register('entity-types', views.EntityTypeViewSet)

urlpatterns = [
    url(r'^ui/', include(router.urls)),
]

for app_name in settings.AETHER_APPS:
    urlpatterns.append(
        url(r'{}/(?P<path>.*)'.format(app_name),
            login_required(tokens_required(views.TokenProxyView.as_view(app_name=app_name))),
            name='{}-proxy'.format(app_name))
    )

app_name = 'api'
