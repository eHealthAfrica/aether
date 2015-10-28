from django.conf.urls import url

from .views import XFormViewSet

urlpatterns = [

    # deliberately choosing this very url here because /formList is ODK collect's default
    url(r'^formList$', XFormViewSet.as_view({'get': 'list'}), name='formtemplate-list'),

    url(r'^form/(?P<pk>[^/.]+)/$', XFormViewSet.as_view({'get': 'retrieve'}), name='formtemplate-detail'),
]
