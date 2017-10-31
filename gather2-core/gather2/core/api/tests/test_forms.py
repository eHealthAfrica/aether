from django.test import TestCase
from .. import forms


class FormsTest(TestCase):

    def test_str_to_json(self):
        data = '{"dob": "2000-01-01", "name":"PersonA"}'
        expected = {'dob': '2000-01-01', 'name': 'PersonA'}
        result = str(forms.str_to_json(data))
        self.assertTrue(str(expected) in result, result)

    def test_str_to_json_no_data(self):
        data = None
        expected = {}
        result = str(forms.str_to_json(data))
        self.assertTrue(str(expected) in result, result)
