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

from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views, views_collect

router = DefaultRouter()

router.register('projects', views.ProjectViewSet)
router.register('xforms', views.XFormViewSet)
router.register('media-files', views.MediaFileViewSet)
router.register('surveyors', views.SurveyorViewSet)


urlpatterns = router.urls + [
    path(route='formList',
         view=views_collect.xform_list,
         name='xform-list-xml'),
    path(route='forms/<slug:pk>/form.xml',
         view=views_collect.xform_get_download,
         name='xform-get-download'),
    path(route='forms/<slug:pk>/manifest.xml',
         view=views_collect.xform_get_manifest,
         name='xform-get-manifest'),
    path(route='media-file/<slug:pk>',
         view=views_collect.media_file_get_content,
         name='media-file-get-content'),
    path(route='submission',
         view=views_collect.xform_submission,
         name='xform-submission'),
]
