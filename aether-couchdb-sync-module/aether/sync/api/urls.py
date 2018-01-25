from django.urls import path

from . import views


app_name = 'sync'

urlpatterns = [
    path('signin', view=views.signin, name='signin'),
]
