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


class ProjectAdmin(CompareVersionAdmin):
    list_display = ('id', 'name', 'revision',)
    readonly_fields = ('id',)


class MappingAdmin(CompareVersionAdmin):
    form = forms.MappingForm
    list_display = ('id', 'name', 'revision',)
    readonly_fields = ('id',)


class MappingSetAdmin(CompareVersionAdmin):
    list_display = ('id', 'name', 'revision', 'project',)
    readonly_fields = ('id',)


class SubmissionAdmin(CompareVersionAdmin):
    form = forms.SubmissionForm
    list_display = ('id', 'revision', 'mappingset',)
    readonly_fields = ('id',)


class SchemaAdmin(CompareVersionAdmin):
    form = forms.SchemaForm
    list_display = ('id', 'name', 'revision',)
    readonly_fields = ('id',)


class ProjectSchemaAdmin(CompareVersionAdmin):
    list_display = ('id', 'name', 'is_encrypted', 'project', 'schema',)
    readonly_fields = ('id',)


class EntityAdmin(CompareVersionAdmin):
    form = forms.EntityForm
    list_display = ('id', 'revision', 'status', 'projectschema',  'submission',)
    readonly_fields = ('id', 'submission',)


admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.MappingSet, MappingSetAdmin)
admin.site.register(models.Mapping, MappingAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.ProjectSchema, ProjectSchemaAdmin)
admin.site.register(models.Entity, EntityAdmin)
