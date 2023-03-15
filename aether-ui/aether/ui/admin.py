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

from django.conf import settings
from django.contrib import admin, messages
from django.utils.translation import gettext as _

from .api import models, utils

if settings.MULTITENANCY:  # pragma: no cover
    PROJECT_LIST_FILTER = (
        ('mt__realm', admin.EmptyFieldListFilter),
        'mt__realm',
    )
    PIPELINE_LIST_FILTER = (
        ('project__mt__realm', admin.EmptyFieldListFilter),
        'project__mt__realm',
    )
    CONTRACT_LIST_FILTER = (
        ('pipeline__project__mt__realm', admin.EmptyFieldListFilter),
        'pipeline__project__mt__realm',
    )

else:  # pragma: no cover
    PROJECT_LIST_FILTER = []
    PIPELINE_LIST_FILTER = []
    CONTRACT_LIST_FILTER = []


class BaseAdmin(admin.ModelAdmin):

    empty_value_display = '---'
    list_per_page = 25
    date_hierarchy = 'modified'
    show_full_result_count = True
    readonly_fields = ('created', 'modified',)


class ProjectAdmin(BaseAdmin):

    def publish(self, request, queryset):
        try:
            for item in queryset:
                utils.publish_project(item)
            self.message_user(
                request,
                _('Published selected projects to Aether Kernel'),
                level=messages.INFO
            )
        except utils.PublishError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    publish.short_description = _('Publish selected projects to Aether Kernel')

    actions = ['publish']

    list_display = ('name', 'project_id', 'is_default',)
    list_filter = ('active',) + PROJECT_LIST_FILTER
    search_fields = list_display
    ordering = list_display


class PipelineAdmin(BaseAdmin):

    def publish(self, request, queryset):
        try:
            for item in queryset:
                utils.publish_pipeline(item)
            self.message_user(
                request,
                _('Published selected pipelines to Aether Kernel'),
                level=messages.INFO
            )
        except utils.PublishError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    publish.short_description = _('Publish selected pipelines to Aether Kernel')

    actions = ['publish']

    list_display = ('name', 'project', 'mappingset',)
    list_filter = PIPELINE_LIST_FILTER
    search_fields = list_display
    ordering = list_display


class ContractAdmin(BaseAdmin):

    def publish(self, request, queryset):
        try:
            for item in queryset:
                utils.publish_contract(item)
            self.message_user(
                request,
                _('Published selected contracts to Aether Kernel'),
                level=messages.INFO
            )
        except utils.PublishError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    publish.short_description = _('Publish selected contracts to Aether Kernel')

    actions = ['publish']

    list_display = (
        'name', 'pipeline', 'published_on', 'mapping',
        'is_active', 'is_read_only',
    )
    list_filter = ('is_active', 'is_read_only',) + CONTRACT_LIST_FILTER
    search_fields = ('name',)
    ordering = list_display

    date_hierarchy = 'published_on'
    readonly_fields = (
        'created', 'modified', 'published_on',
        'mapping_errors', 'output', 'kernel_refs',
    )


admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.Pipeline, PipelineAdmin)
admin.site.register(models.Contract, ContractAdmin)
