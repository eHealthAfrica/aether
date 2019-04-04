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

from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from .api import models, forms


class BaseAdmin(CompareVersionAdmin):
    empty_value_display = '---'
    list_per_page = 25
    readonly_fields = ('id',)
    show_full_result_count = True


class ProjectAdmin(BaseAdmin):
    list_display = ('id', 'name', 'revision',)


class MappingSetAdmin(BaseAdmin):
    form = forms.MappingSetForm
    list_display = ('id', 'name', 'revision', 'project',)


class MappingAdmin(BaseAdmin):
    form = forms.MappingForm
    list_display = ('id', 'name', 'revision', 'mappingset',)


class SubmissionAdmin(BaseAdmin):
    form = forms.SubmissionForm
    list_display = ('id', 'revision', 'mappingset',)


class AttachmentAdmin(BaseAdmin):
    list_display = ('id', 'name', 'md5sum', 'submission',)
    readonly_fields = ('id', 'md5sum',)


class SchemaAdmin(BaseAdmin):
    form = forms.SchemaForm
    list_display = ('id', 'name', 'revision',)


class SchemaDecoratorAdmin(BaseAdmin):
    list_display = ('id', 'name', 'revision', 'project', 'schema',)


class EntityAdmin(BaseAdmin):
    form = forms.EntityForm
    list_display = ('id', 'revision', 'status', 'submission', 'mapping',)


admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.MappingSet, MappingSetAdmin)
admin.site.register(models.Mapping, MappingAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Attachment, AttachmentAdmin)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.SchemaDecorator, SchemaDecoratorAdmin)
admin.site.register(models.Entity, EntityAdmin)
