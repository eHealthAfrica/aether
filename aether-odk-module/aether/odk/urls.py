from django.urls import include, path

from aether.common.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(token=True, kernel=True) + [
    path('', include('aether.odk.api.urls')),
]
