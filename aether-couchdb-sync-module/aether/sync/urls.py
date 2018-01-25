from django.urls import include, path

from aether.common.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(kernel=True) + [
    path('rq/', include('django_rq.urls')),
    path('sync/', include('aether.sync.api.urls', namespace='sync')),
]
