from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from .views import ProxyView


auth_urls = 'rest_framework.urls'
if settings.CAS_SERVER_URL:  # pragma: no cover
    import django_cas_ng.views

    auth_urls = [
        url(r'^login/$', django_cas_ng.views.login, name='login'),
        url(r'^logout/$', django_cas_ng.views.logout, name='logout'),
    ]


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include(auth_urls, namespace='rest_framework')),

    # Proxy to other apps
    url(r'^core/(?P<path>.*)$',
        login_required(ProxyView.as_view(
            base_url=settings.GATHER_CORE_URL,
            token=settings.GATHER_CORE_TOKEN,
        )),
        name='core-proxy'),
    url(r'^odk/(?P<path>.*)$',
        login_required(ProxyView.as_view(
            base_url=settings.GATHER_ODK_URL,
            token=settings.GATHER_ODK_TOKEN,
        )),
        name='odk-proxy'),

    # Entrypoints
    url(r'^$',
        login_required(TemplateView.as_view(template_name='pages/index.html')),
        name='index-page'),

    url(r'^surveys/(?P<action>\w+)/(?P<survey_id>[0-9]+)?$',
        login_required(TemplateView.as_view(template_name='pages/surveys.html')),
        name='surveys'),

    url(r'^surveyors/(?P<action>\w+)/(?P<surveyor_id>[0-9]+)?$',
        login_required(TemplateView.as_view(template_name='pages/surveyors.html')),
        name='surveyors'),
]


if settings.DEBUG:  # pragma: no cover
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
