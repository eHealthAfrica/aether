# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ugettext as _

from .models import Survey, XForm
from .xform_utils import parse_file
from .surveyors_utils import get_surveyors


class SurveyForm(forms.ModelForm):

    surveyors = forms.ModelMultipleChoiceField(
        label=_('Surveyors'),
        help_text=_('Only users with group "surveyor" appear in this list'),
        queryset=get_surveyors(),
        required=False,
        widget=FilteredSelectMultiple(verbose_name=_('users'), is_stacked=False),
    )

    class Meta:
        model = Survey
        fields = (
            'survey_id',
            'name',
            'surveyors',
        )


class SurveyAdmin(admin.ModelAdmin):

    form = SurveyForm
    list_display = (
        'survey_id',
        'name',
    )


class XFormForm(forms.ModelForm):

    xml_file = forms.FileField(
        label=_('XLS Form / XML File'),
        help_text=_('Upload an XLS Form or an XML File'),
        required=False,
    )
    surveyors = forms.ModelMultipleChoiceField(
        label=_('Surveyors'),
        help_text=_('Only users with group "surveyor" appear in this list'),
        queryset=get_surveyors(),
        required=False,
        widget=FilteredSelectMultiple(verbose_name=_('users'), is_stacked=False),
    )

    def clean_xml_data(self):
        if 'xml_file' in self.files:
            return parse_file(
                filename=str(self.files['xml_file']),
                content=self.files['xml_file'].file,
            )
        return self.cleaned_data['xml_data']

    def clean(self):
        cleaned_data = super(XFormForm, self).clean()
        xml_file = cleaned_data.get('xml_file')
        xml_data = cleaned_data.get('xml_data')

        if not (xml_file or xml_data):
            raise forms.ValidationError(
                _('Please upload an XLS Form or an XML File, or enter the XML data.')
            )

    class Meta:
        model = XForm
        fields = [
            'id', 'survey',
            'xml_file', 'xml_data',
            'surveyors', 'description',
        ]


class XFormAdmin(admin.ModelAdmin):

    form = XFormForm
    list_display = (
        'id',
        'survey',
        'title',
        'form_id',
        'description',
        'created_at',
    )
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('title', 'form_id',)

    fieldsets = (
        (_('Gather2 Core'), {
            'description': _('Please choose the Gather2 Core Survey.'),
            'fields': ['survey', 'description', ]
        }),

        (_('xForm definition'), {
            'description': _('Please upload an XLS Form or an XML File, or enter the XML data.'),
            'fields': ['xml_file', 'xml_data', 'title', 'form_id', ],
        }),

        (_('Granted surveyors'), {
            'description': _(
                'If you do not specify any surveyors, EVERYONE will be able to access this xForm.'
            ),
            'fields': ['surveyors', ],
        }),
    )


admin.site.register(Survey, SurveyAdmin)
admin.site.register(XForm, XFormAdmin)
