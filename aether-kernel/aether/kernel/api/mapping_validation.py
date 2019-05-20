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
import json
from django.utils.translation import ugettext as _
import spavro

from .entity_extractor import find_by_jsonpath, ARRAY_ACCESSOR_REGEX


Success = collections.namedtuple('Success', ['path', 'result'])
Failure = collections.namedtuple('Failure', ['path', 'description'])


INVALID_PATH = _(
    'A destination path (the right side of a mapping) must consist of '
    'exactly two parts: <schema-name>.<field-name>. '
    'Example: "Person.firstName"'
)
NO_MATCH = _('No match for path')


def no_schema(schema_name):
    return _('Could not find schema "{}"').format(schema_name)


def invalid_schema(schema_name):
    return _('The schema "{}" is invalid').format(schema_name)


def validate_getter(obj, path):
    '''
    Validate the left side of a mapping pair ("source").
    '''
    if path.startswith('#!'):
        return Success(path, [])
    result = [
        datum.value
        for datum in find_by_jsonpath(obj, path)
    ]
    if result:
        return Success(path, result)
    return Failure(path, NO_MATCH)


def is_array_accessor(field, field_accessor):
    matches = ARRAY_ACCESSOR_REGEX.match(field_accessor)
    return matches.group(0) == field


def always_false(*args, **kwargs):
    return False


def validate_existence_in_fields(field_name, path, definition):
    # looks an a schema object with property fields
    # if field_name matches one of the properties, we mark success
    # if a field_name is a dotted match child.name -> child
    # we recurse and look for a nested object

    # if this field is an array accessor, we'll perform extra checking
    check_array = is_array_accessor \
        if len(ARRAY_ACCESSOR_REGEX.findall(field_name)) > 1 \
        else always_false

    for field in definition['fields']:
        if field['name'] == field_name:
            # matching field exists in this level
            return Success(path, [])
        elif check_array(field['name'], field_name):
            return Success(path, [])
        else:
            # Test for base path matches
            # and recurse if required
            field_parts = field_name.split('.')
            if field['name'] == field_parts[0]:
                child = field.get('type', [])
                if not isinstance(child, dict):  # could be a union, get the dict.
                    try:
                        child = [t for t in field.get('type', []) if isinstance(t, dict)][0]
                    except IndexError:  # no match
                        continue
                next_field_name = '.'.join(field_parts[1:])
                return validate_existence_in_fields(next_field_name, path, child)
    # fail if no matches are found and no new level can be searched.
    return Failure(path, NO_MATCH)


def validate_setter(schemas, path):
    '''
    Validate the right side of a mapping pair ("destination").
    '''
    path_segments = path.split('.')
    try:
        schema_name, field_name = path_segments
    except ValueError:
        # path has a nested property indicated
        schema_name = path_segments[0]
        field_name = '.'.join(path_segments[1:])

    try:
        schema_definition = schemas[schema_name]
    except KeyError:
        message = no_schema(schema_name)
        return Failure(path, message)

    try:
        spavro.schema.parse(json.dumps(schema_definition))
    except spavro.schema.SchemaParseException:
        message = invalid_schema(schema_name)
        return Failure(path, message)

    return validate_existence_in_fields(field_name, path, schema_definition)


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
