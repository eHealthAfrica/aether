# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

import json

from django import forms
from django.utils.translation import ugettext as _

from .models import Schema


class SchemaForm(forms.ModelForm):

    name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}))
    avro_file = forms.FileField(
        label=_('AVRO Schema file'),
        help_text=_('Upload an AVRO Schema file'),
        required=False,
    )

    def clean_avro_schema(self):
        if 'avro_file' in self.files:
            try:
                return json.loads(self.files['avro_file'].file.read())
            except Exception as e:
                raise forms.ValidationError(e)
        return self.cleaned_data['avro_schema']

    def clean(self):
        cleaned_data = super(SchemaForm, self).clean()

        avro_file = cleaned_data.get('avro_file')
        avro_schema = cleaned_data.get('avro_schema')

        if not (avro_file or avro_schema):
            raise forms.ValidationError(
                _('Please upload an AVRO Schema file, or enter the AVRO Schema definition.')
            )

    class Meta:
        model = Schema
        fields = [
            'id', 'project', 'kernel_id', 'name',
            'avro_file', 'avro_schema'
        ]
