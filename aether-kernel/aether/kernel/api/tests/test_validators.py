from django.test import TestCase
from rest_framework import serializers

from aether.kernel.api import validators


class ValidatorsTest(TestCase):

    def setUp(self):
        self.schema = {
            'name': 'Test',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string'
                }
            ]
        }

    def test_is_avro_schema__success(self):
        result = validators.is_avro_schema(self.schema)
        self.assertIsNone(result)

    def test_is_avro_schema__error(self):
        with self.assertRaises(serializers.ValidationError) as err:
            validators.is_avro_schema({})  # "{}" is not a valid Avro schema
        message = str(err.exception.detail[0])
        self.assertIn('No "type" property', message)

    def test_has_valid_id_field__success(self):
        result = validators.has_valid_id_field(self.schema)
        self.assertIsNone(result)

    def test_has_valid_id_field__error(self):
        invalid_schema = {
            'name': 'Test',
            'type': 'record',
            'fields': [
                {
                    'name': 'id',
                    'type': 'int'  # "id" has to be of type "string"
                }
            ]
        }
        with self.assertRaises(serializers.ValidationError) as err:
            validators.has_valid_id_field(invalid_schema)
        message = str(err.exception.detail[0])
        self.assertIn(validators.MESSAGE_REQUIRED_ID, message)
