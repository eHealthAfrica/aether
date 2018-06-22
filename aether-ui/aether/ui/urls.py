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
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from aether.common.conf.urls import generate_urlpatterns


urlpatterns = generate_urlpatterns(kernel=True) + [
    # API
    url(r'^api/', include('aether.ui.api.urls')),

    # Pipeline builder app
    url(r'^$',
        login_required(TemplateView.as_view(template_name='pages/pipeline.html')),
        name='pipeline-app'),

    # styleguide
    url(r'^styleguide/',
        login_required(TemplateView.as_view(template_name='pages/styleguide.html')),
        name='styleguide'),
]
