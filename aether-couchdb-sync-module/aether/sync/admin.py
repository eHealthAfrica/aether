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

from .api.forms import SchemaForm
from .api.models import MobileUser, DeviceDB, Project, Schema
from .api.kernel_utils import (
    KernelPropagationError,
    propagate_kernel_artefacts,
    propagate_kernel_project,
)


class BaseAdmin(admin.ModelAdmin):

    empty_value_display = '---'
    list_per_page = 25
    show_full_result_count = True


class MobileUserAdmin(BaseAdmin):

    list_display = (
        'id',
        'email',
    )
    search_fields = ('email',)
    ordering = list_display


class DeviceDBAdmin(BaseAdmin):

    list_display = (
        'id',
        'device_id',
        'mobileuser',
        'last_synced_seq',
        'last_synced_date',
        'last_synced_log_message',
    )
    readonly_fields = ('last_synced_date', 'last_synced_log_message', )
    search_fields = ('device_id', 'mobileuser')
    ordering = list_display


class ProjectAdmin(BaseAdmin):

    def propagate(self, request, queryset):  # pragma: no cover
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
    )


class SchemaAdmin(BaseAdmin):

    def propagate(self, request, queryset):  # pragma: no cover
        try:
            for item in queryset:
                propagate_kernel_artefacts(item)
            self.message_user(
                request,
                _('Propagated selected schemas to Aether Kernel'),
                level=messages.INFO
            )
        except KernelPropagationError as e:
            self.message_user(request, str(e), level=messages.ERROR)

    propagate.short_description = _('Propagate selected schemas to Aether Kernel')

    actions = ['propagate']
    form = SchemaForm
    list_display = (
        'id',
        'name',
        'project',
        'kernel_id',
    )
    search_fields = ('name', 'kernel_id',)
    ordering = list_display
    readonly_fields = ('avro_schema_prettified',)

    fieldsets = (
        (_('Schema'), {
            'description': _('Please indicate the basic data.'),
            'fields': ['name', 'project', ]
        }),

        (_('Aether Kernel'), {
            'description': _('Please indicate the Aether Kernel artefacts.'),
            'fields': ['kernel_id', ]
        }),

        (_('AVRO definition'), {
            'description': _('Please upload an AVRO Schema file, or enter the AVRO Schema definition.'),
            'fields': ['avro_file', 'avro_schema', ],
        }),
    )


admin.site.register(DeviceDB, DeviceDBAdmin)
admin.site.register(MobileUser, MobileUserAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Schema, SchemaAdmin)
