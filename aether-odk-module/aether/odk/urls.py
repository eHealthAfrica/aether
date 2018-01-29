from django.conf.urls import include, url

from aether.common.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(token=True, kernel=True) + [
    url(r'^', include('aether.odk.api.urls')),
]
