from django.conf.urls import url
from .views import check_kernel


urlpatterns = [
    url(r'^check-kernel', check_kernel, name='check-kernel'),
]
