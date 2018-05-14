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

from .utils import find_by_jsonpath

MESSAGE_NO_MATCH = 'No match for path'

Success = collections.namedtuple('Success', ['path', 'result'])
Failure = collections.namedtuple('Failure', ['path', 'error_message'])


def validate_getter(obj, path):
    if path.startswith('#!'):
        return Success(path, [])
    result = [
        datum.value for datum in
        find_by_jsonpath(obj, path)
    ]
    if result:
        return Success(path, result)
    return Failure(path, MESSAGE_NO_MATCH)


def validate_setter(entity_list, path):
    path_segments = path.split('.')
    schema_name = path_segments[0]
    setter = '.'.join(['$'] + path_segments[1:])
    for entity in entity_list:
        if entity.projectschema_name == schema_name:
            result = [
                datum.value for datum in
                find_by_jsonpath(entity.payload, setter)
            ]
            if result:
                return Success(path, result)
    return Failure(path, MESSAGE_NO_MATCH)


def validate_mapping(submission_payload, entity_list, mapping):
    getter, setter = mapping
    return (
        validate_getter(submission_payload, getter),
        validate_setter(entity_list, setter),
    )


def validate_mappings(submission_payload, entity_list, mapping_definition):
    errors = []
    for mapping in mapping_definition['mapping']:
        for result in validate_mapping(submission_payload, entity_list, mapping):
            if isinstance(result, Failure):
                errors.append(result)
    return errors
