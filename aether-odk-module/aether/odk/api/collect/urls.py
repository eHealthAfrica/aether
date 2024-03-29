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

from django.urls import path

from . import views

urlpatterns = [
    path(route='formList',
         view=views.xform_list,
         name='xform-list-xml'),

    path(route='forms/<slug:pk>/form.xml',
         view=views.xform_get_download,
         name='xform-get-download'),

    path(route='forms/<slug:pk>/manifest.xml',
         view=views.xform_get_manifest,
         name='xform-get-manifest'),

    path(route='media-file/<slug:pk>',
         view=views.media_file_get_content,
         name='media-file-get-content'),

    path(route='submission',
         view=views.xform_submission,
         name='xform-submission'),
]
