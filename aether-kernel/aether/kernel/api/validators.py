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
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

'''
All public functions in this file raise
rest_framework.serializers.ValidationError when validation fails. They are
intended to be used inside of serializer classes to validate incoming data.
'''

import json

from jsonschema.validators import Draft4Validator

from rest_framework import serializers
from spavro.schema import parse, SchemaParseException

MESSAGE_REQUIRED_ID = 'A schema is required to have a field "id" of type "string"'

mapping_definition_schema = {
    'description': (
        'A mapping definition is either an empty object or an object with two '
        'required properties: "entities" and "mapping". '
        'An empty object will not trigger entity extraction.'
    ),
    'oneOf': [
        {
            'type': 'object',
            'additionalProperties': False,
            'properties': {},
        },
        {
            'type': 'object',
            'properties': {
                'entities': {
                    'type': 'object',
                    'patternProperties': {
                        '^[A-Za-z0-9_]+$': {'type': 'string'}
                    }
                },
                'mapping': {
                    'type': 'array',
                    'items': {
                        'type': 'array',
                        'minItems': 2,
                        'maxItems': 2,
                        'items': {
                            'type': 'string'
                        }
                    }
                }
            },
            'required': ['entities', 'mapping']
        }
    ]
}

mapping_definition_validator = Draft4Validator(mapping_definition_schema)


def validate_avro_schema(value):
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
    If top level is a union type, check all child schemas.
    '''
    id_field_type = None
    schema_statuses = []
    if not isinstance(schema, list):
        schemas = [schema]
    else:
        schemas = schema
    for schema in schemas:
        for field in schema.get('fields', []):
            if field.get('name', None) == 'id':
                id_field_type = field.get('type', None)
                break

        schema_statuses.append(id_field_type and id_field_type == 'string')
    # True if All of the statuses were True
    return True in schema_statuses and False not in schema_statuses


def validate_id_field(schema):
    '''
    If ``schema`` does not have a top-level field "id" of type "string", raise
    ``serializers.ValidationError``.
    '''
    if not _has_valid_id_field(schema):
        raise serializers.ValidationError(MESSAGE_REQUIRED_ID)


def validate_mapping_definition(value):
    '''
    If ``value`` does not conform to the mapping definition schema, raise
    ``serializers.ValidationError``.
    '''
    errors = sorted(
        mapping_definition_validator.iter_errors(value),
        key=lambda e: e.path,
    )
    if errors:
        error_messages = [e.message for e in errors]
        raise serializers.ValidationError(error_messages)
