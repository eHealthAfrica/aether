# -*- coding: utf-8 -*-

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

from django.contrib import admin, messages
from django.utils.translation import ugettext as _

from .api.models import Project, XForm, MediaFile
from .api.forms import ProjectForm, XFormForm
from .api.kernel_utils import (
    KernelPropagationError,
    propagate_kernel_artefacts,
    propagate_kernel_project,
)


class BaseAdmin(admin.ModelAdmin):

    empty_value_display = '---'
    list_per_page = 25
    show_full_result_count = True


class ProjectAdmin(BaseAdmin):

    def propagate(self, request, queryset):
        try:
            for item in queryset:
                propagate_kernel_project(item)
            self.message_user(
                request,
                _('Propagated selected projects to Aether Kernel'),
                level=messages.INFO
            )
        except KernelPropagationError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    propagate.short_description = _('Propagate selected projects to Aether Kernel')

    actions = ['propagate']
    form = ProjectForm
    list_display = (
        'project_id',
        'name',
    )
    search_fields = ('name',)
    ordering = list_display

    fieldsets = (
        (_('Aether Kernel'), {
            'description': _('Please choose the Aether Kernel Project.'),
            'fields': ['project_id', 'name', ]
        }),

        (_('Granted surveyors'), {
            'description': _(
                'If you do not specify any surveyors, EVERYONE will be able to access this project xForms.'
            ),
            'fields': ['surveyors', ],
        }),
    )


class XFormAdmin(BaseAdmin):

    def propagate(self, request, queryset):
        try:
            for item in queryset:
                propagate_kernel_artefacts(item)
            self.message_user(
                request,
                _('Propagated selected xForms to Aether Kernel'),
                level=messages.INFO
            )
        except KernelPropagationError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    propagate.short_description = _('Propagate selected xForms to Aether Kernel')

    actions = ['propagate']
    form = XFormForm
    list_display = (
        'id',
        'project',
        'title',
        'form_id',
        'description',
        'created_at',
        'version',
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('title', 'form_id', 'version', 'md5sum', 'avro_schema', 'avro_schema_prettified',)
    search_fields = ('project', 'title', 'form_id',)
    ordering = list_display

    fieldsets = (
        (_('Aether Kernel'), {
            'description': _('Please indicate the Aether Kernel artefacts.'),
            'fields': ['project', 'kernel_id', ]
        }),

        (_('Granted surveyors'), {
            'description': _(
                'If you do not specify any surveyors, EVERYONE will be able to access this xForm.'
            ),
            'fields': ['surveyors', ],
        }),

        (_('xForm definition'), {
            'description': _('Please upload an XLS Form or an XML File, or enter the XML data.'),
            'fields': ['xml_file', 'xml_data', 'description', 'title', 'form_id', 'version', 'avro_schema', ],
        }),
    )


class MediaFileAdmin(BaseAdmin):

    list_display = (
        'xform',
        'name',
        'md5sum',
        'media_file',
    )
    readonly_fields = ('md5sum',)
    search_fields = ('xform', 'name',)
    ordering = list_display


admin.site.register(Project, ProjectAdmin)
admin.site.register(XForm, XFormAdmin)
admin.site.register(MediaFile, MediaFileAdmin)
