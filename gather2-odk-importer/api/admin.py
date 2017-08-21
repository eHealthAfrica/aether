# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms

from .models import XForm
from .xform_utils import parse_xlsform, parse_xmlform


class XFormForm(forms.ModelForm):
    xlsform = forms.FileField(required=False)
    xmlform = forms.FileField(required=False)

    def clean_xml_data(self):
        if 'xlsform' in self.files:
            return parse_xlsform(self.files['xlsform'].file)
        if 'xmlform' in self.files:
            return parse_xmlform(self.files['xmlform'].file)
        return self.cleaned_data['xml_data']

    def clean(self):
        cleaned_data = super(XFormForm, self).clean()
        xlsform = cleaned_data.get('xlsform')
        xmlform = cleaned_data.get('xmlform')
        xml_data = cleaned_data.get('xml_data')

        if not (xlsform or xmlform or xml_data):
            raise forms.ValidationError('Please, specify XForm data or upload an XLSForm/XMLForm.')

    class Meta:
        model = XForm
        fields = [
            'id', 'description',
            'xml_data', 'xlsform', 'xmlform',
            'gather_core_survey_id', 'surveyors',
        ]


class XFormAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'form_id',
        'description',
        'created_at',
    )
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('title', 'form_id',)
    form = XFormForm


admin.site.register(XForm, XFormAdmin)
