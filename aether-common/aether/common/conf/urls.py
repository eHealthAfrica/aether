from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from aether.common.auth.views import obtain_auth_token
from aether.common.conf.views import basic_serve, media_serve
from aether.common.health.views import health
from aether.common.kernel.views import check_kernel


try:  # pragma: no cover
    # Django 2.0+
    from django.urls import include as django_include, re_path as django_path
    django_version = 2

except ImportError as e:  # pragma: no cover
    # Django < 2.0
    from django.conf.urls import include as django_include, url as django_path
    django_version = 1


def include(*args, **kwargs):
    '''
    Shortcut to `django.urls.include` in Django 2.x and `django.conf.urls.include` in Django 1.x.

    Offers compatibility with Django 1.x and 2.x.
    '''

    return django_include(*args, **kwargs)


def url_pattern(path_re, *args, **kwargs):
    '''
    Shortcut to `django.urls.re_path` in Django 2.x and `django.conf.urls.url` in Django 1.x.

    Offers compatibility with Django 1.x and 2.x.
    '''

    return django_path(path_re, *args, **kwargs)


def generate_urlpatterns(token=False, kernel=False):  # pragma: no cover
    '''
    Generates the most common url patterns in the apps.

    Default URLs included:

        - the `/health` URL. Always responds with `200` status and an empty JSON object `{}`.
        - the `/admin` section URLs.
        - the `/accounts` URLs, checks if the REST Framework ones or the UMS ones.
        - the `debug toolbar` URLs only in DEBUG mode.
        - the `/media` URLS. The endpoint gives protected access
          (only logged in users) to media files.
        - the `/media-basic` URLS. The endpoint gives protected access
          (only logged in users with basic authentication) to media files.

    Based on the arguments:

        - `token`: indicates if the app should be able to create and return
                   user tokens via POST request and activates the URL.
                   The url endpoint is `/accounts/token`.

        - `kernel`: indicates if the app should have an URL that checks if
                    Aether Kernel Server is reachable with the provided environment
                    variables `AETHER_KERNEL_URL` and `AETHER_KERNEL_TOKEN`.
                    The url endpoint is `/check-kernel`.

    '''

    auth_urls = 'rest_framework.urls'
    if settings.CAS_SERVER_URL:
        import django_cas_ng.views

        auth_urls = [
            url_pattern(r'^login/$', django_cas_ng.views.login, name='login'),
            url_pattern(r'^logout/$', django_cas_ng.views.logout, name='logout'),
        ]

    if django_version == 1:
        admin_urls = url_pattern(r'^admin/', include(admin.site.urls))
    else:
        admin_urls = url_pattern(r'^admin/', admin.site.urls)

    urlpatterns = [

        # `health` endpoint
        url_pattern(r'^health$', health, name='health'),

        # `admin` section
        admin_urls,

        # `accounts` management
        url_pattern(r'^accounts/', include(auth_urls, namespace='rest_framework')),

        # media files (protected)
        url_pattern(r'^media/(?P<path>.*)$', login_required(media_serve), name='media'),

        # media files (basic auth)
        url_pattern(r'^media-basic/(?P<path>.*)$', basic_serve, name='media-basic'),

    ]

    if settings.DEBUG:
        if 'debug_toolbar' in settings.INSTALLED_APPS:
            import debug_toolbar

            urlpatterns += [
                url_pattern(r'^__debug__/', include(debug_toolbar.urls)),
            ]

    if token:
        # generates users token
        urlpatterns += [
            url_pattern(r'^accounts/token$', obtain_auth_token, name='token'),
        ]

    if kernel:
        # checks if Core server is available
        urlpatterns += [
            url_pattern(r'^check-kernel$', check_kernel, name='check-kernel'),
        ]

    return urlpatterns
