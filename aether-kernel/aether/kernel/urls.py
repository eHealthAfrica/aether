from aether.common.conf.urls import generate_urlpatterns, include, url_pattern
from aether.kernel.api.views import AetherSchemaView


API_PREFIX = '^(?P<version>v1)'


urlpatterns = generate_urlpatterns(token=True) + [
    url_pattern(f'', include('aether.kernel.api.urls')),
    url_pattern(f'{API_PREFIX}/', include('aether.kernel.api.urls')),
    url_pattern(f'{API_PREFIX}/schema/', AetherSchemaView.as_view(), name='api_schema'),
]
