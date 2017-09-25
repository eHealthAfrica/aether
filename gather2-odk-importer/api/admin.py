# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ugettext as _

from .models import Survey, XForm
from .xform_utils import parse_xlsform, parse_xmlform
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

    xlsform = forms.FileField(
        label=_('XLS Form'),
        help_text=_('Upload file with XLS Form definition'),
        required=False,
    )
    xmlform = forms.FileField(
        label=_('XML File'),
        help_text=_('Upload file with XML Data definition'),
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
            raise forms.ValidationError(
                _('Please upload an XLS Form or an XML File, or enter the XML data.')
            )

    class Meta:
        model = XForm
        fields = [
            'id', 'survey',
            'xlsform', 'xmlform', 'xml_data',
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
            'fields': ['survey', ]
        }),

        (_('xForm definition'), {
            'description': _('Please upload an XLS Form or an XML File, or enter the XML data.'),
            'fields': ['xlsform', 'xmlform', 'xml_data', 'title', 'form_id', ],
        }),

        (_('Granted surveyors'), {
            'description': _(
                'If you do not specify any surveyors, EVERYONE will be able to access this xForm.'
            ),
            'fields': ['surveyors', ],
        }),

        (_('Comments'), {
            'fields': ['description', ],
        }),
    )


admin.site.register(Survey, SurveyAdmin)
admin.site.register(XForm, XFormAdmin)
