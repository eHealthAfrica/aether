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

from django.core.exceptions import ValidationError
from aether.python import exceptions, validators


def wrapper_validate_schemas(data):
    '''
    Used to validate:
    - the Entity definitions in the ``validate_mappings_view`` view.

    Checks that each entity definition:
    - is a valid AVRO schema and,
    - is of type "record" and,
    - contains a top-level field "id" of type "string".
    '''
    try:
        return validators.validate_schemas(data)
    except exceptions.ValidationError as ve:
        raise ValidationError(ve.message)


def wrapper_validate_mapping_definition(data):
    '''
    Used to validate:
    - the mapping rules in the ``validate_mappings_view`` view.
    - the mapping rules in the Mapping instances.
    '''
    try:
        return validators.validate_mapping_definition(data)
    except exceptions.ValidationError as ve:
        raise ValidationError(ve)


def wrapper_validate_schema_definition(data):
    '''
    Used to validate:
    - the AVRO schema definition in the Schema instances.

    Checks that the schema definition:
    - is a valid AVRO schema and,
    - is of type "record" and,
    - contains a top-level field "id" of type "string".
    '''
    try:
        return validators.validate_schema_definition(data)
    except exceptions.ValidationError as ve:
        raise ValidationError(ve)


def wrapper_validate_schema_input_definition(data):
    '''
    Used to validate:
    - the AVRO schema derived from an input in the Mapping Set instances.

    Checks that the schema definition:
    - is a valid AVRO schema and,
    - is of type "record".
    '''
    try:
        return validators.validate_schema_input_definition(data)
    except exceptions.ValidationError as ve:
        raise ValidationError(ve.message)
