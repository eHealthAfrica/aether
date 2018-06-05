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

from django.conf.urls import include, url

from aether.common.conf.urls import generate_urlpatterns
from aether.kernel.api.views import AetherSchemaView


API_PREFIX = '^(?P<version>v1)'


urlpatterns = generate_urlpatterns(token=True) + [
    url(r'^', include('aether.kernel.api.urls')),
    url(f'{API_PREFIX}/', include('aether.kernel.api.urls')),
    url(f'{API_PREFIX}/schema/', AetherSchemaView.as_view(), name='api_schema'),
]
