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

from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views
from ..settings import APP_ID

router = DefaultRouter()

router.register('schemas', views.SchemaViewSet)
router.register('projects', views.ProjectViewSet)
router.register('projects-stats', views.ProjectStatsViewSet, base_name='projects_stats')
router.register('projectschemas', views.ProjectSchemaViewSet)
router.register('mappingsets', views.MappingSetViewSet)
router.register('mappingsets-stats', views.MappingSetStatsViewSet, base_name='mappingsets_stats')
router.register('mappings', views.MappingViewSet)
router.register('submissions', views.SubmissionViewSet)
router.register('attachments', views.AttachmentViewSet)
router.register('entities', views.EntityViewSet)


urlpatterns = router.urls + [
    url(r'^validate-mappings/$', views.validate_mappings_view, name='validate-mappings'),
]
# Prepend urls with /kernel/
urlpatterns = [url(fr'^{APP_ID}/', include(urlpatterns))]