# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import XForm


class XFormAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'title',
        'description',
        'created_at',
    )
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('title',)


admin.site.register(XForm, XFormAdmin)
