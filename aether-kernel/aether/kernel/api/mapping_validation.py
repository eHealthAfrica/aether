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

import collections
import json

from .utils import find_by_jsonpath

import spavro

Success = collections.namedtuple('Success', ['path', 'result'])
Failure = collections.namedtuple('Failure', ['path', 'description'])


INVALID_PATH = (
    'A destination path (the right side of a mapping) must consist of '
    'exactly two parts: <schema-name>.<field-name>. '
    'Example: "Person.firstName"'
)
NO_MATCH = 'No match for path'


def no_schema(schema_name):
    return 'Could not find schema "{schema_name}"'.format(
        schema_name=schema_name
    )


def invalid_schema(schema_name):
    return 'The schema "{schema_name}" is invalid'.format(
        schema_name=schema_name
    )


def validate_getter(obj, path):
    '''
    Validate the left side of a mapping pair ("source").
    '''
    if path.startswith('#!'):
        return Success(path, [])
    result = [
        datum.value for datum in
        find_by_jsonpath(obj, path)
    ]
    if result:
        return Success(path, result)
    return Failure(path, NO_MATCH)


def validate_setter(schemas, path):
    '''
    Validate the right side of a mapping pair ("destination").
    '''
    path_segments = path.split('.')
    try:
        schema_name, field_name = path_segments
    except ValueError as e:
        return Failure(path, INVALID_PATH)

    try:
        schema_definition = schemas[schema_name]
    except KeyError as e:
        message = no_schema(schema_name)
        return Failure(path, message)

    try:
        spavro.schema.parse(json.dumps(schema_definition))
    except spavro.schema.SchemaParseException as e:
        message = invalid_schema(schema_name)
        return Failure(path, message)

    for field in schema_definition['fields']:
        if field['name'] == field_name:
            return Success(path, [])

    return Failure(path, NO_MATCH)


def validate_mapping(submission_payload, entities, mapping):
    getter, setter = mapping
    return (
        validate_getter(submission_payload, getter),
        validate_setter(entities, setter),
    )


def validate_mappings(submission_payload, schemas, mapping_definition):
    '''
    Given an arbitrarily shaped submission_payload and a list of entities,
    accumulate a list of the lookup errors (if any) which would occur when
    applying the mappings to them.

    This is primarily used by the aether-ui module via the validate_mappings
    view.
    '''
    errors = []
    for mapping in mapping_definition['mapping']:
        for result in validate_mapping(submission_payload, schemas, mapping):
            if isinstance(result, Failure):
                errors.append(result)
    return errors


