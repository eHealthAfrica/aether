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

import collections
import uuid
import json
import gettext

from spavro.schema import parse

from .tools import AvroValidator, format_validation_error

_ = gettext.gettext

MESSAGE_NOT_UUID = _('Entity id "{}" is not a valid uuid')


EntityValidationResult = collections.namedtuple(
    'EntityValidationResult',
    ['validation_errors', 'entities'],
)


def validate_avro(schema, datum):
    result = AvroValidator(
        schema=parse(json.dumps(schema)),
        datum=datum,
    )
    errors = []
    for error in result.errors:
        errors.append({
            'description': format_validation_error(error),
        })
    return errors


def validate_entity_payload_id(entity_payload):
    id_ = entity_payload.get('id', None)
    try:
        uuid.UUID(id_, version=4)
        return None
    except (ValueError, AttributeError, TypeError):
        return {'description': MESSAGE_NOT_UUID.format(id_)}


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
