from django.urls import include, path, re_path

from aether.common.conf.urls import generate_urlpatterns
from aether.kernel.api.views import AetherSchemaView


API_PREFIX = '^(?P<version>v1)'


urlpatterns = generate_urlpatterns(token=True) + [
    path(f'', include('aether.kernel.api.urls')),
    re_path(f'{API_PREFIX}/', include('aether.kernel.api.urls')),
    re_path(f'{API_PREFIX}/schema/', AetherSchemaView.as_view(), name='api_schema'),
]
