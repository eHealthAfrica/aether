from django.conf.urls import url
from .views import obtain_auth_token


urlpatterns = [
    url(r'^token', obtain_auth_token, name='token'),
]
