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
This module contains an alternative implementation of the validate()
function from the official avro python library. See class docstring
for details.
'''

import collections

# Constants used by AvroValidator to distinguish between avro types
# ``int`` and ``long``.
INT_MIN_VALUE = -(1 << 31)
INT_MAX_VALUE = (1 << 31) - 1
LONG_MIN_VALUE = -(1 << 63)
LONG_MAX_VALUE = (1 << 63) - 1

# Avro type names
ARRAY = 'array'
BOOLEAN = 'boolean'
BYTES = 'bytes'
DOUBLE = 'double'
ENUM = 'enum'
ERROR = 'error'
ERROR_UNION = 'error_union'
FIXED = 'fixed'
FLOAT = 'float'
INT = 'int'
LONG = 'long'
MAP = 'map'
NULL = 'null'
RECORD = 'record'
REQUEST = 'request'
STRING = 'string'
UNION = 'union'


class AvroValidationException(Exception):
    pass


# This namedtuple represents an avro validation error.
# Fields:
#     - expected: the expected type.
#     - datum: the actual value.
#     - path: the location of the error, notated as a jsonpath.
#
# Example:
#     AvroValidationError(expected=['null', 'string'], datum=1, path='$.a.b')
#
#     indicates that the expected type at path "$.a.b" was a union of
#     'null' and 'string'. The actual value was 1.
AvroValidationError = collections.namedtuple(
    'AvroValidationError',
    ['expected', 'datum', 'path'],
)


def format_validation_error(error):
    '''
    Format an AvroValidationError.
    '''
    return f'Expected type "{error.expected}" at path "{error.path}". Actual value: {error.datum}'


class AvroValidator(object):
    '''
    AvroValidator validates an avro datum (value) against a schema and
    accumulates a list of all errors.

    This implementation is based on the official avro.io.validate() function,
    which can be found here:
    https://github.com/apache/avro/blob/b71dcf24f252da5858bd95bfd4bd56402e3a458c/lang/py3/avro/io.py#L96-L142.

    avro.io.validate() only returns a boolean which indicates the outcome of
    the validation. No error details are returned. In contrast, this class will
    accumulate a list of all errors encountered during validation.

    The type of AvroValidator.errors is a list of AvroValidationErrors.

    Performance: running AvroValidator.validate() will be about twice as slow
    as avro.io.validate(). AvroValidator.validate() will check 10000 datums
    against a moderately complex schema in ~1 second. avro.io.validate() will
    finish in ~0.5 seconds.
    '''
    def __init__(self, schema, datum, path=None):
        self.errors = []
        if path is None:
            path = AvroValidator.get_initial_path(schema)
        self.is_valid = self.validate(schema, datum, path)

    @staticmethod
    def get_initial_path(schema):
        if hasattr(schema, 'name'):
            return schema.name
        return '$'

    @staticmethod
    def get_schema_typename(schema):
        '''
        Get a string representation of a schema typename.
        '''
        # "union" is a compound avro type without a unique name. Since we would
        # like our errors to contain type information about the subschemas
        # without including their error details, we return a list of all
        # subschema names.
        if schema.type == 'union':
            return [
                AvroValidator.get_schema_typename(s) for s in schema.schemas
            ]
        # Use the schema name if possible. This applies to types like enums and
        # records, the names of which are unique in the context of an avro
        # schema.
        if hasattr(schema, 'name'):
            return schema.name
        # Primitive types have no names; use `schema.type` instead.
        return schema.type

    def on_error(self, schema, datum, path):
        '''
        Add a single error to ``self.errors`` and return ``False`` to indicate
        failed validation.
        '''
        typename = AvroValidator.get_schema_typename(schema)
        error = AvroValidationError(expected=typename, datum=datum, path=path)
        self.errors.append(error)
        return False

    def validate_null(self, schema, datum, path):
        '''Validate ``datum`` against a 'null' schema.'''
        if datum is None:
            return True
        return self.on_error(schema, datum, path)

    def validate_boolean(self, schema, datum, path):
        '''Validate ``datum`` against a 'boolean' schema.'''
        if isinstance(datum, bool):
            return True
        return self.on_error(schema, datum, path)

    def validate_bytes(self, schema, datum, path):
        '''Validate ``datum`` against a 'bytes' schema.'''
        if isinstance(datum, bytes):
            return True
        return self.on_error(schema, datum, path)

    def validate_string(self, schema, datum, path):
        '''Validate ``datum`` against a 'string' schema.'''
        if isinstance(datum, str):
            return True
        return self.on_error(schema, datum, path)

    def validate_int(self, schema, datum, path):
        '''
        Validate ``datum`` against an 'int' schema.
        Check that the value of ``datum`` is within the integer range.
        '''
        if (isinstance(datum, int) and INT_MIN_VALUE <= datum <= INT_MAX_VALUE):
            return True
        return self.on_error(schema, datum, path)

    def validate_long(self, schema, datum, path):
        '''
        Validate ``datum`` against a 'long' schema.
        Check that the value of ``datum`` is within the long range.
        '''
        if (isinstance(datum, int) and LONG_MIN_VALUE <= datum <= LONG_MAX_VALUE):
            return True
        return self.on_error(schema, datum, path)

    def validate_float(self, schema, datum, path):
        '''Validate ``datum`` against a 'float' schema.'''
        if (isinstance(datum, int) or isinstance(datum, float)):
            return True
        return self.on_error(schema, datum, path)

    def validate_fixed(self, schema, datum, path):
        '''Validate ``datum`` against a 'fixed' schema.'''
        if isinstance(datum, str) and len(datum) == schema.size:
            return True
        return self.on_error(schema, datum, path)

    def validate_enum(self, schema, datum, path):
        '''Validate ``datum`` against an 'enum' schema.'''
        if datum in schema.symbols:
            return True
        return self.on_error(schema, datum, path)

    def validate_array(self, schema, datum, path):
        '''
        Validate ``datum`` against an 'array' schema.
        Accumulate any validation errors in ``schema.items``.
        '''
        if not isinstance(datum, list):
            return self.on_error(schema, datum, path)
        result = []
        for i, item in enumerate(datum):
            subpath = f'{path}[{i}]'
            result.append(self.validate(schema.items, item, subpath))
        return all(result)

    @staticmethod
    def is_maplike(datum):
        '''
        Return ``True`` if ``datum`` is a dict and all its keys are strings.
        '''
        return (isinstance(datum, dict) and
                all([isinstance(key, str) for key in datum.keys()]))

    def validate_map(self, schema, datum, path):
        '''
        Validate ``datum`` against an 'map' schema.
        Accumulate any validation errors in ``schema.values``.
        '''
        if not AvroValidator.is_maplike(datum):
            return self.on_error(schema, datum, path)
        result = []
        for value in datum.values():
            result.append(self.validate(schema.values, value, path))
        return all(result)

    def validate_union(self, schema, datum, path):
        '''
        Validate ``datum`` against a 'union' schema.
        Any errors encountered when validating subschemas are discarded.
        Instead, we append an error indicating that the validation of the union
        itself failed. The advantage of this approach is that **most** error
        messages will be more helpful; instead of several separate error
        messages, each indicating validation failure in a subschema, we will
        get a single error message indicating that the expected type was a
        union of several types. The disadvantage is that we lose some error
        details for complex types.
        '''
        subschema_errors = []
        for subschema in schema.schemas:
            # Any errors encountered during subschema validation will be
            # discarded, so we need a separate validation state for each
            # subschema.
            validator = AvroValidator(subschema, datum, path)
            if validator.errors:
                subschema_errors.extend(validator.errors)
            else:
                # Stop iteration as soon as we encounter a subschema without
                # errors -- at this point, we know that ``datum`` is valid.
                subschema_errors = []
                break
        if subschema_errors:
            self.on_error(schema, datum, path)
            return False
        return True

    def validate_record(self, schema, datum, path):
        '''
        Validate ``datum`` against a 'record' schema.
        '''
        if not isinstance(datum, dict):
            return self.on_error(schema, datum, path)
        result = []
        for f in schema.fields:
            new_path = f'{path}.{f.name}'
            result.append(self.validate(f.type, datum.get(f.name), new_path))
        return all(result)

    def validate(self, schema, datum, path):
        '''
        Validate ``datum`` against ``schema``.
        '''
        if schema.type == NULL:
            return self.validate_null(schema, datum, path)
        if schema.type == BOOLEAN:
            return self.validate_boolean(schema, datum, path)
        if schema.type == STRING:
            return self.validate_string(schema, datum, path)
        if schema.type == BYTES:
            return self.validate_bytes(schema, datum, path)
        if schema.type == LONG:
            return self.validate_long(schema, datum, path)
        if schema.type == INT:
            return self.validate_int(schema, datum, path)
        if schema.type in [FLOAT, DOUBLE]:
            return self.validate_float(schema, datum, path)
        if schema.type == FIXED:
            return self.validate_fixed(schema, datum, path)
        if schema.type == ENUM:
            return self.validate_enum(schema, datum, path)
        if schema.type == ARRAY:
            return self.validate_array(schema, datum, path)
        if schema.type == MAP:
            return self.validate_map(schema, datum, path)
        if schema.type in [UNION, ERROR_UNION]:
            return self.validate_union(schema, datum, path)
        if schema.type in [RECORD, ERROR, REQUEST]:
            return self.validate_record(schema, datum, path)
        raise AvroValidationException(
            f'Could not validate datum "{datum}" against "{schema}"'
        )


def validate(schema, data):
    '''
    Wrap AvroValidator in a function. Returns an instance of AvroValidator.
    '''
    return AvroValidator(schema, data)
