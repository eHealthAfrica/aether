# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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
from django.urls import include, path, re_path

from aether.sdk.conf.urls import generate_urlpatterns
from aether.kernel.views import AetherSchemaView
from aether.kernel.api.entity_extractor import extract_view

API_PREFIX = '^(?P<version>v1)'


urlpatterns = generate_urlpatterns(token=True, app=[
    path(route='', view=include('aether.kernel.api.urls')),
    re_path(route=f'{API_PREFIX}/', view=include('aether.kernel.api.urls')),

    re_path(route=f'{API_PREFIX}/schema/',
            view=AetherSchemaView.without_ui(cache_timeout=0),
            name='api_schema'),
    re_path(route=f'{API_PREFIX}/swagger/$',
            view=AetherSchemaView.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'),

    path(route=f'{settings.ADMIN_URL}/~extract', view=extract_view, name='admin-extract'),
])
