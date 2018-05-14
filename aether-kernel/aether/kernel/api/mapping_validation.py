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
Failure = collections.namedtuple('Failure', ['path', 'description'])


class JsonpathValidationError(object):
    def __init__(self, description, path):
        self.description = description
        self.path = path

    @classmethod
    def from_failure(self, failure):
        return JsonpathValidationError(
            description=failure.description,
            path=failure.path,
        )

    def as_dict(self):
        return {
            'description': self.description,
            'path': self.path,
            'type': self.__class__.__name__,
        }


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


def validate_setter(entities, path):
    path_segments = path.split('.')
    schema_name = path_segments[0]
    setter = '.'.join(['$'] + path_segments[1:])
    for entity in entities:
        if entity.projectschema_name == schema_name:
            result = [
                datum.value for datum in
                find_by_jsonpath(entity.payload, setter)
            ]
            if result:
                return Success(path, result)
    return Failure(path, MESSAGE_NO_MATCH)


def validate_mapping(submission_payload, entities, mapping):
    getter, setter = mapping
    return (
        validate_getter(submission_payload, getter),
        validate_setter(entities, setter),
    )


def validate_mappings(submission_payload, entities, mapping_definition):
    errors = []
    for mapping in mapping_definition['mapping']:
        for result in validate_mapping(submission_payload, entities, mapping):
            if isinstance(result, Failure):
                error = JsonpathValidationError.from_failure(result).as_dict()
                errors.append(error)
    return errors
