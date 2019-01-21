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

from .api.views import signin, load_file
from .views import check_rq


urlpatterns = generate_urlpatterns(token=True, kernel=True) + [
    url(r'^', include('aether.sync.api.urls')),

    url(r'^check-rq$', view=check_rq, name='check-rq'),
    url(r'^rq/', include('django_rq.urls')),

    # used by the Aether Mobile App
    url(r'^sync/signin$', view=signin, name='signin'),
    # simulate the sync process using an Aether Mobile App backup file
    url(r'^sync/load-file$', view=load_file, name='load-file'),
]
