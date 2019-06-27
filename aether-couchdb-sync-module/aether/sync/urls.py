# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.urls import include, path

from aether.sdk.conf.urls import generate_urlpatterns

from .api.views import signin, load_file
from .views import check_rq


urlpatterns = generate_urlpatterns(token=True, app=[
    path('', include('aether.sync.api.urls')),

    path('check-rq', view=check_rq, name='check-rq'),
    path('rq/', include('django_rq.urls')),

    # used by the Aether Mobile App
    path('sync/signin', view=signin, name='signin'),

    # simulate the sync process using an Aether Mobile App backup file
    path('sync/load-file', view=load_file, name='load-file'),
])
