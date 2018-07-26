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
from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url

from aether.common.auth.views import obtain_auth_token
from aether.common.conf.views import basic_serve, media_serve
from aether.common.health.views import health, check_db
from aether.common.kernel.views import check_kernel
from aether.common.kernel.utils import get_kernel_server_url


def generate_urlpatterns(token=False, kernel=False):  # pragma: no cover
    '''
    Generates the most common url patterns in the apps.

    Default URLs included:

        - the `/health` URL. Always responds with `200` status and an empty JSON object `{}`.
        - the `/check-db` URL. Responds with `500` status if the database is not available.
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
            url(r'^login/$', django_cas_ng.views.login, name='login'),
            url(r'^logout/$', django_cas_ng.views.logout, name='logout'),
        ], 'rest_framework')

    urlpatterns = [
        # `health` endpoints
        url(r'^health$', health, name='health'),
        url(r'^check-db$', check_db, name='check-db'),

        # `admin` section
        url(r'^admin/', admin.site.urls),

        # `accounts` management
        url(r'^accounts/', include(auth_urls, namespace='rest_framework')),

        # media files (protected)
        url(r'^media/(?P<path>.*)$', login_required(media_serve), name='media'),

        # media files (basic auth)
        url(r'^media-basic/(?P<path>.*)$', basic_serve, name='media-basic'),

        # monitoring
        url('', include('django_prometheus.urls')),
    ]

    if settings.DEBUG:
        if 'debug_toolbar' in settings.INSTALLED_APPS:
            import debug_toolbar

            urlpatterns += [
                url(r'^__debug__/', include(debug_toolbar.urls)),
            ]

    if token:
        # generates users token
        urlpatterns += [
            url('^accounts/token$', obtain_auth_token, name='token'),
        ]

    if kernel:
        # checks if Kernel server is available
        urlpatterns += [
            url('^check-kernel$', check_kernel, name='check-kernel'),
        ]

        # `aether.common.kernel.utils.get_kernel_server_url()` returns different
        #  values depending on the value of `settings.TESTING`. Without these
        # assertions, a deployment configuration missing e.g. `AETHER_KERNEL_URL`
        # will seem to be in order until `get_kernel_server_url()` is called.
        if settings.TESTING:
            msg = 'Environment variable "AETHER_KERNEL_URL_TEST" is not set'
        else:
            msg = 'Environment variable "AETHER_KERNEL_URL" is not set'
        assert get_kernel_server_url(), msg

    return urlpatterns
