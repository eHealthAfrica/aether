from django.conf.urls import url

from . import views


app_name = 'sync'

urlpatterns = [
    url(r'^signin$', view=views.signin, name='signin'),
]
