# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.translation import ugettext as _

from .api.models import Mapping, XForm, MediaFile
from .api.forms import MappingForm, XFormForm


class MappingAdmin(admin.ModelAdmin):

    form = MappingForm
    list_display = (
        'mapping_id',
        'name',
    )
    search_fields = ('name',)
    ordering = list_display


class XFormAdmin(admin.ModelAdmin):

    form = XFormForm
    list_display = (
        'id',
        'mapping',
        'title',
        'form_id',
        'description',
        'created_at',
        'version',
    )
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('title', 'form_id', 'version',)
    search_fields = ('mapping', 'title', 'form_id',)
    ordering = list_display

    fieldsets = (
        (_('Aether Kernel'), {
            'description': _('Please choose the Aether Kernel Mapping.'),
            'fields': ['mapping', 'description', ]
        }),

        (_('xForm definition'), {
            'description': _('Please upload an XLS Form or an XML File, or enter the XML data.'),
            'fields': ['xml_file', 'xml_data', 'title', 'form_id', 'version', ],
        }),

        (_('Granted surveyors'), {
            'description': _(
                'If you do not specify any surveyors, EVERYONE will be able to access this xForm.'
            ),
            'fields': ['surveyors', ],
        }),
    )


class MediaFileAdmin(admin.ModelAdmin):

    list_display = (
        'xform',
        'name',
        'md5sum',
        'media_file',
    )
    readonly_fields = ('md5sum',)
    search_fields = ('xform', 'name',)
    ordering = list_display


admin.site.register(Mapping, MappingAdmin)
admin.site.register(XForm, XFormAdmin)
admin.site.register(MediaFile, MediaFileAdmin)
