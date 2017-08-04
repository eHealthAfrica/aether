from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView


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

    # Entrypoints
    url(r'^$',
        login_required(TemplateView.as_view(template_name='pages/index.html')),
        name='index-page'),

    url(r'^search$',
        login_required(TemplateView.as_view(template_name='pages/index.html')),
        name='search'),

    url(r'^surveys/$',
        login_required(TemplateView.as_view(template_name='pages/index.html')),
        name='surveys-list'),
    url(r'^surveys/manage$',
        login_required(TemplateView.as_view(template_name='pages/index.html')),
        name='manage-survey'),
]


if settings.DEBUG:  # pragma: no cover
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
