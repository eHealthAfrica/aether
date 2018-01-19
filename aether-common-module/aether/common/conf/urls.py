from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from aether.common.auth.views import obtain_auth_token
from aether.common.conf.views import basic_serve, media_serve
from aether.common.health.views import health
from aether.common.kernel.views import check_kernel


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

        auth_urls = ([
            path('login/', django_cas_ng.views.login, name='login'),
            path('logout/', django_cas_ng.views.logout, name='logout'),
        ], 'rest_framework')

    urlpatterns = [

        # `health` endpoint
        path('health', health, name='health'),

        # `admin` section
        path('admin/', admin.site.urls),

        # `accounts` management
        path('accounts/', include(auth_urls, namespace='rest_framework')),

        # media files (protected)
        path('media/<path:path>', login_required(media_serve), name='media'),

        # media files (basic auth)
        path('media-basic/<path:path>', basic_serve, name='media-basic'),

    ]

    if settings.DEBUG:
        if 'debug_toolbar' in settings.INSTALLED_APPS:
            import debug_toolbar

            urlpatterns += [
                path('__debug__/', include(debug_toolbar.urls)),
            ]

    if token:
        # generates users token
        urlpatterns += [
            path('accounts/token', obtain_auth_token, name='token'),
        ]

    if kernel:
        # checks if Core server is available
        urlpatterns += [
            path('check-kernel', check_kernel, name='check-kernel'),
        ]

    return urlpatterns
