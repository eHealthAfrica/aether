from django.conf.urls import include, url

from aether.common.conf.urls import generate_urlpatterns
from aether.kernel.api.views import AetherSchemaView, setup_kong_consumer

urlpatterns = generate_urlpatterns(token=True) + [
    url(r'^', include('aether.kernel.api.urls')),
    url(r'^schema/', AetherSchemaView.as_view(), name='api_schema'),
    # provision kong consumer credentials
    url(r'^token$', setup_kong_consumer, name='token'),
]
