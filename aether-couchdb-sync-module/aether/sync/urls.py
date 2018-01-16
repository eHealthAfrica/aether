from aether.common.conf.urls import generate_urlpatterns, include, url_pattern


urlpatterns = generate_urlpatterns(kernel=True) + [

    url_pattern(r'^rq/', include('django_rq.urls')),
    url_pattern(r'^sync/', include('aether.sync.api.urls', 'sync')),

]
