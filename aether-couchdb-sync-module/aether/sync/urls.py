from django.conf.urls import include, url

from aether.common.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(kernel=True) + [
    url(r'^rq/', include('django_rq.urls')),
    url(r'^sync/', include('aether.sync.api.urls', namespace='sync')),
]
