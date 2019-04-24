# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import ugettext as _

from aether.common.health.views import health, check_db, check_app


def generate_urlpatterns(token=False, kernel=False, app=[]):
    '''
    Generates the most common url patterns in the apps.

    Default URLs included:

        - the `/health` URL. Always responds with `200` status and an empty JSON object `{}`.
        - the `/check-db` URL. Responds with `500` status if the database is not available.
        - the `/check-app` URL. Responds with current app version and more.
        - the `/admin` section URLs.
        - the `/accounts` URLs, checks if the REST Framework ones, using the templates
          indicated in `LOGIN_TEMPLATE` and `LOGGED_OUT_TEMPLATE` environment variables,
          or the CAS ones.
        - the `debug toolbar` URLs only in DEBUG mode.

    Based on the arguments:

        - `token`: indicates if the app should be able to create and return
                   user tokens via POST request and activates the URL.
                   The url endpoint is `/accounts/token`.

        - `kernel`: indicates if the app should have an URL that checks if
                    Aether Kernel Server is reachable with the provided environment
                    variables `AETHER_KERNEL_URL` and `AETHER_KERNEL_TOKEN`.
                    The url endpoint is `/check-kernel`.

    '''

    if kernel:  # bail out ASAP
        __check_kernel_env()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # APP specific
    urlpatterns = app

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # HEALTH checks
    urlpatterns += _get_health_urls(kernel)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # KEYCLOAK GATEWAY endpoints
    if settings.GATEWAY_SERVICE_ID:
        urlpatterns = [
            # this is reachable using internal network
            path(route='', view=include(urlpatterns)),
            # this is reachable using the gateway server
            path(route=f'<slug:realm>/{settings.GATEWAY_SERVICE_ID}/', view=include(urlpatterns)),
        ]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # AUTHORIZATION management
    urlpatterns += _get_auth_urls(token)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ADMIN management
    urlpatterns += _get_admin_urls()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # DEBUG toolbar
    urlpatterns += _get_debug_urls()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # nesting app urls
    app_url = settings.APP_URL[1:]  # remove leading slash
    if app_url:
        # Prepend url endpoints with "{APP_URL}/"
        # if APP_URL = "/aether-app" then `<my-server>/aether-app/<endpoint-url>`
        # if APP_URL = "/"           then `<my-server>/<endpoint-url>`
        urlpatterns = [
            path(route=f'{app_url}/', view=include(urlpatterns)),
        ]

    return urlpatterns


def _get_health_urls(kernel):
    health_urls = [
        path(route='health', view=health, name='health'),
        path(route='check-db', view=check_db, name='check-db'),
        path(route='check-app', view=check_app, name='check-app'),
    ]

    if kernel:
        from aether.common.kernel.views import check_kernel

        # checks if Kernel server is available
        health_urls += [
            path(route='check-kernel', view=check_kernel, name='check-kernel'),
        ]

    return health_urls


def _get_auth_urls(token):
    if settings.CAS_SERVER_URL:
        from django_cas_ng import views

        login_view = views.LoginView.as_view()
        logout_view = views.LogoutView.as_view()

    else:
        from django.contrib.auth.views import LoginView, LogoutView

        if not settings.KEYCLOAK_SERVER_URL:
            logout_view = LogoutView.as_view(template_name=settings.LOGGED_OUT_TEMPLATE)
            login_view = LoginView.as_view(template_name=settings.LOGIN_TEMPLATE)

        else:
            from aether.common.keycloak.views import KeycloakLogoutView

            logout_view = KeycloakLogoutView.as_view(template_name=settings.LOGGED_OUT_TEMPLATE)

            if not settings.KEYCLOAK_BEHIND_SCENES:
                from aether.common.keycloak.forms import RealmForm
                from aether.common.keycloak.views import KeycloakLoginView

                login_view = KeycloakLoginView.as_view(
                    template_name=settings.KEYCLOAK_TEMPLATE,
                    authentication_form=RealmForm,
                )
            else:
                from aether.common.keycloak.forms import RealmAuthenticationForm

                login_view = LoginView.as_view(
                    template_name=settings.KEYCLOAK_BEHIND_TEMPLATE,
                    authentication_form=RealmAuthenticationForm,
                )

    auth_urls = [
        path(route='login/', view=login_view, name='login'),
        path(route='logout/', view=logout_view, name='logout'),
    ]

    if token:
        from aether.common.auth.views import obtain_auth_token

        # generates users token
        auth_urls += [
            path(route='token', view=obtain_auth_token, name='token'),
        ]

    ns = 'rest_framework'
    return [
        path(route=f'{settings.AUTH_URL}/', view=include((auth_urls, ns), namespace=ns)),
        path(route='logout/', view=logout_view, name='logout'),
    ]


def _get_admin_urls():
    admin_urls = [
        # monitoring
        path(route='prometheus/', view=include('django_prometheus.urls')),
        # uWSGI monitoring
        path(route='uwsgi/', view=include('django_uwsgi.urls')),
        # `admin` section
        path(route='', view=admin.site.urls),
    ]

    return [
        path(route=f'{settings.ADMIN_URL}/', view=include(admin_urls)),
    ]


def _get_debug_urls():  # pragma: no cover
    if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        return [
            path(route=f'{settings.DEBUG_TOOLBAR_URL}/', view=include(debug_toolbar.urls)),
        ]
    return []


def __check_kernel_env():
    from aether.common.kernel.utils import get_kernel_server_url, get_kernel_server_token

    # `aether.common.kernel.utils.get_kernel_server_url()` returns different
    # values depending on the value of `settings.TESTING`. Without these
    # assertions, a deployment configuration missing e.g. `AETHER_KERNEL_URL`
    # will seem to be in order until `get_kernel_server_url()` is called.
    ERR_MSG = _('Environment variable "{}" is not set')

    key = 'AETHER_KERNEL_URL_TEST' if settings.TESTING else 'AETHER_KERNEL_URL'
    assert get_kernel_server_url(), ERR_MSG.format(key)

    msg_token = ERR_MSG.format('AETHER_KERNEL_TOKEN')
    assert get_kernel_server_token(), msg_token
