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

from django.conf import settings
from django.contrib import admin

from .api import models

if settings.MULTITENANCY:  # pragma: no cover
    PROJECT_LIST_FILTER = ('mt__realm',)
    CHILD_LIST_FILTER = ('project__mt__realm', 'project__active',)
    ATTACH_LIST_FILTER = ('submission__project__mt__realm', 'submission__project__active',)
else:  # pragma: no cover
    PROJECT_LIST_FILTER = []
    CHILD_LIST_FILTER = ('project__active',)
    ATTACH_LIST_FILTER = ('submission__project__active',)


class BaseAdmin(admin.ModelAdmin):
    date_hierarchy = 'modified'
    empty_value_display = '---'
    list_per_page = 25
    readonly_fields = ('id', 'created', 'modified',)
    show_full_result_count = True


class ProjectAdmin(BaseAdmin):
    list_display = ('id', 'name',)
    list_filter = ('active',) + PROJECT_LIST_FILTER


class MappingSetAdmin(BaseAdmin):
    list_display = ('id', 'name', 'revision', 'project',)
    list_filter = CHILD_LIST_FILTER


class MappingAdmin(BaseAdmin):
    list_display = ('id', 'name', 'revision', 'mappingset',)
    list_filter = ('is_active', 'is_read_only',) + CHILD_LIST_FILTER


class SubmissionAdmin(BaseAdmin):
    list_display = ('id', 'mappingset', 'is_extracted',)
    list_filter = ('is_extracted',) + CHILD_LIST_FILTER


class AttachmentAdmin(BaseAdmin):
    list_display = ('id', 'name', 'md5sum', 'submission',)
    readonly_fields = ('id', 'md5sum',)
    list_filter = ATTACH_LIST_FILTER


class SchemaAdmin(BaseAdmin):
    list_display = ('id', 'name', 'family',)


class SchemaDecoratorAdmin(BaseAdmin):
    list_display = ('id', 'name', 'project', 'schema',)
    list_filter = CHILD_LIST_FILTER


class EntityAdmin(BaseAdmin):
    date_hierarchy = 'created'
    list_display = ('id', 'status', 'submission', 'mapping',)
    list_filter = ('status',) + CHILD_LIST_FILTER


class ExportTaskAdmin(BaseAdmin):
    list_display = (
        'id', 'project', 'created', 'created_by',
        'status_records', 'status_attachments',
    )
    readonly_fields = ('id', 'name',)
    list_filter = CHILD_LIST_FILTER


admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.MappingSet, MappingSetAdmin)
admin.site.register(models.Mapping, MappingAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Attachment, AttachmentAdmin)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.SchemaDecorator, SchemaDecoratorAdmin)
admin.site.register(models.Entity, EntityAdmin)
admin.site.register(models.ExportTask, ExportTaskAdmin)
