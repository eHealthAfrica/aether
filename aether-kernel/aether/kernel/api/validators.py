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

import collections
import json
import uuid

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from jsonschema.validators import Draft4Validator

from spavro.io import validate
from spavro.schema import parse, SchemaParseException

from . import avro_tools


MESSAGE_REQUIRED_ID = _('A schema is required to have a field "id" of type "string"')
MESSAGE_NOT_OBJECT = _('Value {} is not an Object')
MESSAGE_NOT_UUID = _('Entity id "{}" is not a valid uuid')
MESSAGE_NOT_VALID = _('Extracted record did not conform to registered schema')

MAPPING_DEFINITION_SCHEMA = {
    'description': _(
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

mapping_definition_validator = Draft4Validator(MAPPING_DEFINITION_SCHEMA)

EntityValidationResult = collections.namedtuple(
    'EntityValidationResult',
    ['validation_errors', 'entities'],
)


def validate_avro_schema(value):
    '''
    Attempt to parse ``value`` into an Avro schema.
    Raise ``ValidationError`` on error.
    '''
    try:
        parse(json.dumps(value))
    except SchemaParseException as e:
        raise ValidationError(str(e))


def _has_valid_id_field(schema):
    '''
    Check if ``schema`` has a top-level field "id" of type "string".
    If top level is a union type, check all child schemas.
    '''

    if isinstance(schema, list):
        schemas = [s for s in schema if s.get('aetherBaseSchema')]
        if len(schemas) != 1:
            return False
        schema = schemas[0]

    for field in schema.get('fields', []):
        if field.get('name', None) == 'id':
            return field.get('type', None) == 'string'

    return False


def validate_id_field(schema):
    '''
    If ``schema`` does not have a top-level field "id" of type "string",
    raise ``ValidationError``.
    '''
    if not _has_valid_id_field(schema):
        raise ValidationError(MESSAGE_REQUIRED_ID)


def validate_schema_definition(value):
    '''
    Attempt to parse ``value`` into an Avro schema and checks if it has
    a top-level field "id" of type "string.
    Raise ``ValidationError`` on error.
    '''
    validate_avro_schema(value)
    validate_id_field(value)


def validate_mapping_definition(value):
    '''
    If ``value`` does not conform to the mapping definition schema,
    raise ``ValidationError``.
    '''
    errors = sorted(
        mapping_definition_validator.iter_errors(value),
        key=lambda e: e.path,
    )
    if errors:
        raise ValidationError([e.message for e in errors])


def validate_schemas(value):
    if not isinstance(value, dict):
        raise ValidationError(MESSAGE_NOT_OBJECT.format(value))

    for schema in value.values():
        validate_schema_definition(schema)

    return value


def validate_entity_payload(schema_definition, payload):
    # Use spavro to validate payload against the linked schema
    try:
        avro_schema = parse(json.dumps(schema_definition))
        valid = validate(avro_schema, payload)
        if not valid:
            raise ValidationError(MESSAGE_NOT_VALID)
        return True
    except Exception as err:
        raise ValidationError(str(err))


def validate_entity_payload_id(entity_payload):
    id_ = entity_payload.get('id', None)
    try:
        uuid.UUID(id_, version=4)
        return None
    except (ValueError, AttributeError, TypeError):
        return {'description': MESSAGE_NOT_UUID.format(id_)}


def validate_avro(schema, datum):
    result = avro_tools.AvroValidator(
        schema=parse(json.dumps(schema)),
        datum=datum,
    )
    errors = []
    for error in result.errors:
        errors.append({
            'description': avro_tools.format_validation_error(error),
        })
    return errors


def validate_entities(entities, schemas):
    validation_errors = []
    validated_entities = collections.defaultdict(list)
    for entity_name, entity_payloads in entities.items():
        for entity_payload in entity_payloads:
            entity_errors = []
            id_error = validate_entity_payload_id(entity_payload)
            if id_error:
                entity_errors.append(id_error)
            schema_definition = schemas[entity_name]
            avro_validation_errors = validate_avro(
                schema=schema_definition,
                datum=entity_payload,
            )
            entity_errors.extend(avro_validation_errors)
            if entity_errors:
                validation_errors.extend(entity_errors)
            else:
                validated_entities[entity_name].append(entity_payload)

    return EntityValidationResult(
        validation_errors=validation_errors,
        entities=validated_entities,
    )
