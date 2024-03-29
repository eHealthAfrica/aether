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

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from .models import Project, XForm
from .xform_utils import parse_xform_file
from .surveyors_utils import get_surveyors


class ProjectForm(forms.ModelForm):

    surveyors = forms.ModelMultipleChoiceField(
        label=_('Surveyors'),
        help_text=_('Only users with group "surveyor" appear in this list'),
        queryset=get_surveyors(),
        required=False,
        widget=FilteredSelectMultiple(verbose_name=_('users'), is_stacked=False),
    )

    class Meta:
        model = Project
        fields = (
            'project_id',
            'name',
            'surveyors',
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
            return parse_xform_file(
                filename=str(self.files['xml_file']),
                content=self.files['xml_file'].file,
            )
        return self.cleaned_data['xml_data']

    def clean(self):
        cleaned_data = super(XFormForm, self).clean()
        xml_file = cleaned_data.get('xml_file')
        xml_data = cleaned_data.get('xml_data')

        if not (xml_file or xml_data):
            raise ValidationError(
                _('Please upload an XLS Form or an XML File, or enter the XML data.'),
                code='required',
            )

    def validate_unique(self):
        try:
            # the default method exclude `form_id` and `version`
            # because they are not in the form fields list
            # (are calculated from `xml_data` value)
            self.instance.validate_unique()
        except ValidationError as e:
            self._update_errors(e)

    class Meta:
        model = XForm
        fields = [
            'id', 'project', 'kernel_id',
            'xml_file', 'xml_data',
            'surveyors', 'description',
        ]
