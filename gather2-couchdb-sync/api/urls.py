from django.conf.urls import url
from . import views

from django.http import HttpResponse


def detail(request):
    return HttpResponse("You're looking at url %s." % request.build_absolute_uri('/api/detail'))


urlpatterns = [
    url(r'^signin', view=views.signin, name='signin'),
    # this is a debug thing to check that request.build_absolute_uri returns the right thing
    # , remove this later when the deployment is working
    url(r'^reflect', view=detail, name='reflect'),
]
