from aether.common.conf.urls import generate_urlpatterns, include, url_pattern


urlpatterns = generate_urlpatterns(token=True, kernel=True) + [
    url_pattern(r'', include('aether.odk.api.urls')),
]
