from django.conf.urls import url
from .views import check_core


urlpatterns = [
    url(r'^check-core', check_core, name='check-core'),
]
