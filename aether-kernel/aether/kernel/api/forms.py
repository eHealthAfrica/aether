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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json

from django import forms
from django.core.exceptions import ValidationError

from .utils import json_printable


def str_to_json(value):
    if value:
        return json_printable(json.loads(value))
    return {}


class JSONField(forms.CharField):   # pragma: no cover
    '''
    Custom form field to represent JSON values
    '''
    widget = forms.Textarea

    def prepare_value(self, value):
        # Serialize value (a Python object)
        # to a JSON formatted str
        if value:
            return json.dumps(value, sort_keys=True, indent=2)
        return '{}'

    def clean(self, value):
        # Deserialize value (a str, bytes or bytearray instance containing a JSON document)
        # to a Python object
        try:
            return str_to_json(value)
        except Exception as e:
            raise ValidationError('Invalid JSON format {}'.format(str(e)))


class MappingForm(forms.ModelForm):
    definition = JSONField()


class SubmissionForm(forms.ModelForm):
    payload = JSONField()


class SchemaForm(forms.ModelForm):
    definition = JSONField()


class EntityForm(forms.ModelForm):
    payload = JSONField()
