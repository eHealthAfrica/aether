from django.conf.urls import include, url

urlpatterns = [
    url(r'', include('aether.common.auth.urls')),
    url(r'', include('aether.common.core.urls')),
]
