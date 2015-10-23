import re

from xml.dom import minidom

from django.contrib import admin
from django import forms
from django.db import models
from django.forms.widgets import Widget
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.encoding import force_text

from .models import FormTemplate

class ReadOnlyXMLWidget(Widget):

    def render(self, name, value, attrs=None):

        if value is None:
            value = ''

        value = re.compile("\n[\t\s]+\n").sub("\n", value)

        final_attrs = self.build_attrs(
            attrs,
            name=name,
            style="white-space: pre-wrap; font-family: monospace")

        return format_html('<p{}>{}</p>',
                           flatatt(final_attrs),
                           force_text(value))

class FormTemplateCreateForm(forms.ModelForm):

    upload = forms.FileField(widget=admin.widgets.AdminFileWidget)

    class Meta:
        model = FormTemplate
        exclude = ['source', ]

class FormTemplateAdmin(admin.ModelAdmin):

    readonly_fields = ('created_by',)
    list_display = ('name', 'description', 'created_by', 'created_at',)

    formfield_overrides = {
        models.TextField: {'widget': ReadOnlyXMLWidget},
    }

    def save_model(self, request, obj, form, change):
        obj.source = minidom.parseString(request.FILES['upload'].read()).toprettyxml()
        obj.created_by = request.user
        obj.save()

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            kwargs['form'] = FormTemplateCreateForm
            kwargs['exclude'] = ['source', 'created_by', ]

        return super(FormTemplateAdmin, self).get_form(request, obj, **kwargs)

admin.site.register(FormTemplate, FormTemplateAdmin)
