'''
All public functions in this file raise
rest_framework.serializers.ValidationError when validation fails. They are
intended to be used inside of serializer classes to validate incoming data.
'''

import json

from rest_framework import serializers
from spavro.schema import parse, SchemaParseException

MESSAGE_REQUIRED_ID = 'A schema is required to have a field "id" of type "string"'


def is_avro_schema(value):
    '''
    Attempt to parse ``value`` into an Avro schema.
    Raise ``serializers.ValidationError`` on error.
    '''
    try:
        parse(json.dumps(value))
    except SchemaParseException as e:
        raise serializers.ValidationError(str(e))


def _has_valid_id_field(schema):
    '''
    Check if ``schema`` has a top-level field "id" of type "string".
    '''
    id_field_type = None
    for field in schema.get('fields', []):
        if field.get('name', None) == 'id':
            id_field_type = field.get('type', None)
            break
    return id_field_type and id_field_type == 'string'


def has_valid_id_field(schema):
    '''
    If ``schema`` does not have a top-level field "id" of type "string", raise
    ``serializers.ValidationError``.
    '''
    if not _has_valid_id_field(schema):
        raise serializers.ValidationError(MESSAGE_REQUIRED_ID)
