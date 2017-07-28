import json

from django import forms
from django.core.exceptions import ValidationError


class JSONField(forms.CharField):   # pragma: no cover
    '''
    Custom form field to represent JSON values
    '''
    widget = forms.Textarea

    def prepare_value(self, value):
        if value:
            return json.dumps(value, sort_keys=True, indent=2)
        return value

    def clean(self, value):
        try:
            return json.loads(value)
        except Exception as e:
            raise ValidationError('Invalid JSON format {}'.format(str(e)))


class SurveyForm(forms.ModelForm):
    schema = JSONField(initial='{}')


class ResponseForm(forms.ModelForm):
    data = JSONField()
