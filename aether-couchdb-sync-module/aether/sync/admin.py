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

from .api.models import MobileUser, DeviceDB, Schema


class MobileUserAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'email',
    )
    search_fields = ('email',)
    ordering = list_display


class DeviceDBAdmin(admin.ModelAdmin):

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


class SchemaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'kernel_id',
    )
    search_fields = ('name', 'kernel_id',)
    ordering = list_display


admin.site.register(MobileUser, MobileUserAdmin)
admin.site.register(DeviceDB, DeviceDBAdmin)
admin.site.register(Schema, SchemaAdmin)
