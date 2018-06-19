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
