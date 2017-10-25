from django.conf.urls import include, url

urlpatterns = [
    url(r'', include('gather2.common.auth.urls')),
    url(r'', include('gather2.common.core.urls')),
]
