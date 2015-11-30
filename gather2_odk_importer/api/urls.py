from django.conf.urls import url

from api import views

urlpatterns = [
    url(r'^(?P<username>\w+)/formList$', views.XFormListView.as_view(), name='xformlistview'),
    url(r'^(?P<username>\w+)/forms/(?P<pk>[^/]+)/form\.xml$', views.XFormXMLView.as_view(), name='download_xform'),
    url(r'^(?P<username>\w+)/forms/create$', views.XFormCreateView.as_view(), name='xformcreate'),
    url(r"^(?P<username>\w+)/xformsManifest/(?P<id_string>[^/]+)$", views.XFormManifestView.as_view(), name='xform_manifest'),
]

###########################################################################
# The following are the urls from formhubs odk_importer app that we need to
# replicate here
###########################################################################

# r"^submission$"
# r"^(?P<username>\w+)/formList$"
# r"^(?P<username>\w+)/xformsManifest/(?P<id_string>[^/]+)$
# r"^(?P<username>\w+)/submission$"
# r"^(?P<username>\w+)/bulk-submission$"
# r"^(?P<username>\w+)/bulk-submission-form$"
# r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xml$"
# r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.xls$"
# r"^(?P<username>\w+)/forms/(?P<id_string>[^/]+)/form\.json"
# r"^(?P<username>\w+)/delete/(?P<id_string>[^/]+)/$"
# r"^(?P<username>\w+)/(?P<id_string>[^/]+)/toggle_form_active/$"
