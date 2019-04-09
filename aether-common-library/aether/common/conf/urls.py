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

    urlpatterns = []

    # `accounts` management
    if settings.CAS_SERVER_URL:
        from django_cas_ng import views

        login_view = views.LoginView.as_view()
        logout_view = views.LogoutView.as_view()

    else:
        from django.contrib.auth.views import LoginView, LogoutView

        logout_view = LogoutView.as_view(template_name=settings.LOGGED_OUT_TEMPLATE)
        if not settings.KEYCLOAK_SERVER_URL:
            login_view = LoginView.as_view(template_name=settings.LOGIN_TEMPLATE)

        else:
            from aether.common.keycloak.forms import RealmForm, RealmAuthenticationForm
            from aether.common.keycloak.views import KeycloakLoginView

            if not settings.KEYCLOAK_BEHIND_SCENES:
                login_view = KeycloakLoginView.as_view(
                    template_name=settings.KEYCLOAK_TEMPLATE,
                    authentication_form=RealmForm,
                )
            else:
                login_view = LoginView.as_view(
                    template_name=settings.KEYCLOAK_BEHIND_TEMPLATE,
                    authentication_form=RealmAuthenticationForm,
                )

    auth_views = [
        path(route='login/', view=login_view, name='login'),
        path(route='logout/', view=logout_view, name='logout'),
    ]

    if token:
        from aether.common.auth.views import obtain_auth_token

        # generates users token
        auth_views += [
            path(route='token', view=obtain_auth_token, name='token'),
        ]
    auth_urls = (auth_views, 'rest_framework')

    urlpatterns += [
        # `health` endpoints
        path(route='health', view=health, name='health'),
        path(route='check-db', view=check_db, name='check-db'),
        path(route='check-app', view=check_app, name='check-app'),

        # `admin` section
        path(route='admin/uwsgi/', view=include('django_uwsgi.urls')),
        path(route='admin/', view=admin.site.urls),

        # `accounts` management
        path(route='accounts/', view=include(auth_urls, namespace='rest_framework')),

        # monitoring
        path(route='', view=include('django_prometheus.urls')),
    ]

    if kernel:
        from aether.common.kernel.views import check_kernel
        from aether.common.kernel.utils import get_kernel_server_url, get_kernel_server_token

        # checks if Kernel server is available
        urlpatterns += [
            path(route='check-kernel', view=check_kernel, name='check-kernel'),
        ]

        # `aether.common.kernel.utils.get_kernel_server_url()` returns different
        #  values depending on the value of `settings.TESTING`. Without these
        # assertions, a deployment configuration missing e.g. `AETHER_KERNEL_URL`
        # will seem to be in order until `get_kernel_server_url()` is called.
        ERR_MSG = _('Environment variable "{}" is not set')

        key = 'AETHER_KERNEL_URL_TEST' if settings.TESTING else 'AETHER_KERNEL_URL'
        assert get_kernel_server_url(), ERR_MSG.format(key)

        msg_token = ERR_MSG.format('AETHER_KERNEL_TOKEN')
        assert get_kernel_server_token(), msg_token

    # add app specific
    urlpatterns += app

    if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:  # pragma: no cover
        import debug_toolbar

        urlpatterns += [
            path(route='__debug__/', view=include(debug_toolbar.urls)),
        ]

    app_url = settings.APP_URL[1:]  # remove leading slash
    if app_url:
        # Prepend url endpoints with "{APP_URL}/"
        # if APP_URL = "/aether-app" then
        # all the url endpoints will be  `<my-server>/aether-app/<endpoint-url>`
        # before they were  `<my-server>/<endpoint-url>`
        urlpatterns = [
            path(route=f'{app_url}/', view=include(urlpatterns)),
        ]

    return urlpatterns
