import json

from django import forms
from django.core.exceptions import ValidationError

from .models import Survey
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


class SurveyForm(forms.ModelForm):
    schema_file = forms.FileField(required=False)
    schema = JSONField(required=False, initial={})

    def clean_schema(self):
        if 'schema_file' in self.files:
            return str_to_json(self.files['schema_file'].file.read())

        return self.cleaned_data['schema']

    class Meta:
        model = Survey
        fields = ['id', 'name', 'created_by', 'schema', 'schema_file', ]


class ResponseForm(forms.ModelForm):
    data = JSONField()
