from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from .views import TokenProxyView, tokens_required
from gather2.common.core.views import check_core


auth_urls = 'rest_framework.urls'
if settings.CAS_SERVER_URL:  # pragma: no cover
    import django_cas_ng.views

    auth_urls = [
        url(r'^login/$', django_cas_ng.views.login, name='login'),
        url(r'^logout/$', django_cas_ng.views.logout, name='logout'),
    ]


urlpatterns = [
    # ----------------------
    # Common entries
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include(auth_urls, namespace='rest_framework')),
    url(r'^check-core$', check_core, name='check-core'),

    # ----------------------
    # Proxy to Gather2 Core
    url(r'^core/(?P<path>.*)$',
        login_required(TokenProxyView.as_view(app_name='core')),
        name='core-proxy'),

    # ----------------------
    # Entrypoints

    # ----------------------
    # Welcome page (WIP)
    url(r'^$',
        login_required(TemplateView.as_view(template_name='pages/index.html')),
        name='index-page'),

    # ----------------------
    # shows error if the user app tokens are not valid
    url(r'^tokens$',
        login_required(TemplateView.as_view(template_name='pages/tokens.html')),
        name='tokens'),

    # ----------------------
    # Gather2 entrypoints
    # Any entry here needs the decorator `tokens_required` if it's going to execute
    # AJAX request to any of the other apps
    url(r'^surveys/(?P<action>\w+)/(?P<mapping_id>[0-9]+)?$',
        tokens_required(TemplateView.as_view(template_name='pages/surveys.html')),
        name='surveys'),

]

if settings.GATHER_ODK:  # pragma: no cover
    urlpatterns += [
        # Proxy to other odk-importer
        url(r'^odk/(?P<path>.*)$',
            login_required(TokenProxyView.as_view(app_name='odk-importer')),
            name='odk-proxy'),
        # Entry point with `tokes_required` test.
        url(r'^surveyors/(?P<action>\w+)/(?P<surveyor_id>[0-9]+)?$',
            tokens_required(TemplateView.as_view(template_name='pages/surveyors.html')),
            name='surveyors'),
    ]


if settings.DEBUG:  # pragma: no cover
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
