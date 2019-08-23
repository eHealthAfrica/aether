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

import uuid

from django.core.exceptions import ValidationError
from unittest import TestCase

from .. import entity_extractor

from . import (EXAMPLE_MAPPING, EXAMPLE_MAPPING_EDGE, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA,
               EXAMPLE_DATA_FOR_NESTED_SCHEMA, EXAMPLE_REQUIREMENTS_NESTED_SCHEMA,
               EXAMPLE_NESTED_SOURCE_DATA, EXAMPLE_REQUIREMENTS, EXAMPLE_REQUIREMENTS_ARRAY_BASE,
               EXAMPLE_ENTITY_DEFINITION, EXAMPLE_FIELD_MAPPINGS, EXAMPLE_FIELD_MAPPINGS_EDGE,
               EXAMPLE_ENTITY, EXAMPLE_FIELD_MAPPINGS_ARRAY_BASE, EXAMPLE_PARTIAL_WILDCARDS)


class EntityExtractorTests(TestCase):

    def test_get_field_mappings(self):
        mapping = EXAMPLE_MAPPING
        expected = EXAMPLE_FIELD_MAPPINGS
        field_mapping = str(entity_extractor.get_field_mappings(mapping))
        self.assertTrue(str(expected) in field_mapping, field_mapping)

    def test_get_field_mappings__edge(self):
        mapping = EXAMPLE_MAPPING_EDGE
        expected = EXAMPLE_FIELD_MAPPINGS_EDGE
        field_mapping = str(entity_extractor.get_field_mappings(mapping))
        self.assertTrue(str(expected) in field_mapping, field_mapping)

    def test_JSP_get_basic_fields(self):
        avro_obj = EXAMPLE_SCHEMA
        expected = ['id', '_rev', 'name', 'dob', 'villageID']
        basic_fields = str(entity_extractor.JSP_get_basic_fields(avro_obj))
        self.assertTrue(str(expected) in basic_fields, basic_fields)

    def test_get_entity_definitions(self):
        entity_type = 'Person'
        mapping = EXAMPLE_MAPPING
        schema = {entity_type: EXAMPLE_SCHEMA}
        expected = EXAMPLE_ENTITY_DEFINITION
        entity_definition = str(entity_extractor.get_entity_definitions(mapping, schema))
        self.assertTrue(str(expected) in entity_definition, entity_definition)

    def test_get_entity_requirements(self):
        entities = EXAMPLE_ENTITY_DEFINITION
        field_mappings = EXAMPLE_FIELD_MAPPINGS
        expected = EXAMPLE_REQUIREMENTS
        entity_requirements = str(
            entity_extractor.get_entity_requirements(entities, field_mappings))
        self.assertTrue(str(expected) in entity_requirements,
                        entity_requirements)

    def test_get_entity_requirements__union_base(self):
        entities = EXAMPLE_ENTITY_DEFINITION
        field_mappings = EXAMPLE_FIELD_MAPPINGS_ARRAY_BASE
        expected = EXAMPLE_REQUIREMENTS_ARRAY_BASE
        entity_requirements = str(
            entity_extractor.get_entity_requirements(entities, field_mappings))
        self.assertTrue(str(expected) in entity_requirements,
                        entity_requirements)

    def test_get_entity_stub(self):
        requirements = EXAMPLE_REQUIREMENTS
        source_data = EXAMPLE_SOURCE_DATA
        entity_definitions = EXAMPLE_ENTITY_DEFINITION
        entity_name = 'Person'
        stub = entity_extractor.get_entity_stub(
            requirements, entity_definitions, entity_name, source_data)
        self.assertEqual(len(stub.get('dob')), 3)

    def test_nest_object__simple_object(self):
        obj = {}
        path = 'a.b.c'
        value = 1
        entity_extractor.nest_object(obj, path, value)
        self.assertEqual(obj['a']['b']['c'], value)

    def test_nest_object__unlikely_dotted_reference(self):
        obj = {'a.b': 2, 'a.b.c': None}
        path = 'a.b.c'
        value = 1
        entity_extractor.nest_object(obj, path, value)
        self.assertEqual(obj['a']['b']['c'], value)
        self.assertEqual(obj['a.b'], 2)

    def test_put_nested__simple_object(self):
        keys = ['a', 'b', 'c']
        obj = entity_extractor.put_nested({}, keys, 1)
        self.assertEqual(obj['a']['b']['c'], 1)

    def test_put_nested__array(self):
        keys = ['a', 'b', 'c', 'de[0]']
        obj = entity_extractor.put_nested({}, keys, 1)
        self.assertEqual(obj['a']['b']['c']['de'][0], 1)

    def test_put_in_array__simple(self):
        obj = None
        val = 'a'
        obj = entity_extractor.put_in_array(obj, 0, val)
        self.assertEqual(obj[0], val)

    def test_put_in_array__existing_value(self):
        starting = 1
        obj = [starting]
        val = 'a'
        obj = entity_extractor.put_in_array(obj, 0, val)
        self.assertEqual(obj[0], val)
        self.assertEqual(obj[1], starting)

    def test_put_in_array__large_idx(self):
        obj = None
        val = 'a'
        obj = entity_extractor.put_in_array(obj, 100, val)
        self.assertEqual(obj[0], val)

    def test_resolve_source_reference__single_resolution(self):
        data = EXAMPLE_SOURCE_DATA
        requirements = EXAMPLE_REQUIREMENTS
        entities = EXAMPLE_ENTITY
        entity_name = 'Person'
        field = 'villageID'
        path = requirements.get(entity_name, {}).get(field)[0]
        resolved_count = entity_extractor.resolve_source_reference(
            path, entities, entity_name, 0, field, data)
        self.assertEqual(resolved_count, 1)

    def test_resolve_source_reference__multiple_resolutions(self):
        data = EXAMPLE_SOURCE_DATA
        requirements = EXAMPLE_REQUIREMENTS
        entities = EXAMPLE_ENTITY
        entity_name = 'Person'
        field = 'dob'
        path = requirements.get(entity_name, {}).get(field)[0]
        resolved_count = entity_extractor.resolve_source_reference(
            path, entities, entity_name, 0, field, data)
        self.assertEqual(resolved_count, 3)

    def test_resolve_source_reference__wildcard_resolutions(self):
        data = EXAMPLE_SOURCE_DATA
        entities = EXAMPLE_ENTITY
        entity_name = 'Person'
        field = 'dob'
        path = 'data.pe*[*].dob'
        resolved_count = entity_extractor.resolve_source_reference(
            path, entities, entity_name, 0, field, data)
        self.assertEqual(resolved_count, 3)

    def test_resolve_source_reference__nested_schema(self):
        data = EXAMPLE_DATA_FOR_NESTED_SCHEMA
        requirements = EXAMPLE_REQUIREMENTS_NESTED_SCHEMA
        entities = {'Nested': [{}, {}, {}]}
        entity_name = 'Nested'
        field = 'location.lat'
        path = requirements.get(entity_name, {}).get(field)
        resolved_count = entity_extractor.resolve_source_reference(
            path, entities, entity_name, 0, field, data)
        self.assertEqual(resolved_count, 3)

    def test_keyed_object_partial_wildcard(self):
        data = EXAMPLE_PARTIAL_WILDCARDS
        bad_path = '$households[0].name*'  # missing '.' after $
        try:
            entity_extractor.find_by_jsonpath(data, bad_path)
        except ValidationError:
            pass
        else:
            self.fail('Should have thrown an error')
        expected = [
            ('$.households[0].name*', 2),
            ('$.households[1].name*', 1),
            ('$.households[*].name*', 3),
            ('$.households[0].name1', 1),
            ('$.households[*].name1', 2)
        ]
        for path, matches in expected:
            self.assertEqual(len(entity_extractor.find_by_jsonpath(data, path)), matches), (path, matches)

    def test_coercion(self):
        test_cases = [
            ('a', 'string', 'a'),
            ('true', 'boolean', True),
            ('True', 'boolean', True),
            ('T', 'boolean', True),
            ('0', 'boolean', True),
            (0, 'boolean', False),
            (1, 'string', '1'),
            ('1', 'json', 1),
            (1, 'int', 1),
            ('1', 'int', 1),
            ('1.00', 'float', 1.00),
            ('["a"]', 'json', ['a']),
            ('{"hold": ["a"]}', 'json', {'hold': ['a']})
        ]
        for t in test_cases:
            res = entity_extractor.coerce(t[0], t[1])
            self.assertTrue(res == t[2])
        try:
            entity_extractor.coerce('a_string', 'float')
        except ValueError:
            pass
        else:
            self.fail('Should have thrown an error')

    def test_action_none(self):
        self.assertTrue(entity_extractor.action_none() is None)

    def test_action_constant(self):
        args = ['154', 'int']
        self.assertTrue(entity_extractor.action_constant(args) == 154)
        self.assertTrue(entity_extractor.action_constant(['154']) == '154')
        try:
            entity_extractor.action_constant(['a', 'bad_type'])
        except ValueError:
            pass
        else:
            self.fail('Should have thrown a type error on unsupported type')

    def test_anchor_references(self):
        source_data = EXAMPLE_NESTED_SOURCE_DATA
        source = 'data.houses[*].people[*]'
        context = 'data.houses[*]'
        instance_number = 5
        idx = entity_extractor.anchor_reference(
            source, context, source_data, instance_number)
        self.assertEqual(idx, 1), 'Person #5 be found in second house, index @ 1'

    def test_get_or_make_uuid(self):
        entity_type = 'Person'
        field_name = '_id'
        instance_number = 0
        source_data = EXAMPLE_SOURCE_DATA
        uuid = str(entity_extractor.get_or_make_uuid(
            entity_type, field_name, instance_number, source_data))
        self.assertEqual(uuid.count('-'), 4)

    def test_extractor_action__entity_reference(self):
        source_path = '#!entity-reference#bad-reference'
        try:
            entity_extractor.extractor_action(
                source_path, None, None, None, None, None)
            self.assertTrue(False)
        except ValueError:
            self.assertTrue(True)

    def test_extractor_action__none(self):
        source_path = '#!none'
        res = entity_extractor.extractor_action(
            source_path, None, None, None, None, None)
        self.assertEqual(res, None)

    def test_extractor_action__constant(self):
        source_path = '#!constant#1#int'
        res = entity_extractor.extractor_action(
            source_path, None, None, None, None, None)
        self.assertEqual(res, 1)

    def test_extractor_action__missing(self):
        source_path = '#!undefined#1#int'
        try:
            entity_extractor.extractor_action(
                source_path, None, None, None, None, None)
            self.assertTrue(False)
        except ValueError:
            self.assertTrue(True)

    def test_extract_entity(self):
        requirements = EXAMPLE_REQUIREMENTS
        response_data = EXAMPLE_SOURCE_DATA
        entity_definitions = EXAMPLE_ENTITY_DEFINITION
        expected_entity = EXAMPLE_ENTITY
        entities = {'Person': []}
        entity_name = 'Person'
        entity_stub = entity_extractor.get_entity_stub(
            requirements, entity_definitions, entity_name, response_data
        )
        failed_actions = entity_extractor.extract_entity(
            entity_name, entities, requirements, response_data, entity_stub
        )
        self.assertEqual(
            len(expected_entity['Person']), len(entities['Person']))
        self.assertEqual(len(failed_actions), 0)

    def test_extract_entities(self):
        '''
        Assert that the number of extracted entities equals the
        number of Persons in the source data.
        '''
        requirements = EXAMPLE_REQUIREMENTS
        response_data = EXAMPLE_SOURCE_DATA
        entity_stubs = EXAMPLE_ENTITY_DEFINITION
        schemas = {'Person': EXAMPLE_SCHEMA}
        submission_data, entities = entity_extractor.extract_entities(
            requirements,
            response_data,
            entity_stubs,
            schemas,
        )
        expected_entity = EXAMPLE_ENTITY
        self.assertEqual(
            len(expected_entity['Person']), len(entities['Person']))

    def test_extract_create_entities__no_requirements(self):
        '''
        If the mapping contains neither paths nor entity references, no
        entities can be extracted.
        '''
        submission_payload = EXAMPLE_SOURCE_DATA
        mapping_definition = {'mapping': [], 'entities': {}}
        schemas = {}
        submission_data, entities = entity_extractor.extract_create_entities(
            submission_payload,
            mapping_definition,
            schemas,
        )
        submission_errors = submission_data['aether_errors']
        self.assertEqual(len(submission_errors), 0)
        self.assertEqual(len(entities), 0)

    def test_extract_create_entities__success(self):
        '''
        Assert that no errors are accumulated and that the
        extracted entities are of the expected type.
        '''
        submission_payload = EXAMPLE_SOURCE_DATA
        mapping_definition = EXAMPLE_MAPPING
        schemas = {'Person': EXAMPLE_SCHEMA}
        submission_data, entities = entity_extractor.extract_create_entities(
            submission_payload,
            mapping_definition,
            schemas,
        )
        submission_errors = submission_data['aether_errors']
        self.assertEqual(len(submission_errors), 0)
        self.assertTrue(len(entities) > 0)
        for entity in entities:
            self.assertIn(entity.schemadecorator_name, schemas.keys())
            self.assertEqual(entity.status, 'Publishable')

    def test_extract_create_entities__validation_error(self):
        '''
        Assert that validation errors are accumulated and that they contain
        information about the non-validating entities.
        '''
        submission_payload = EXAMPLE_SOURCE_DATA
        mapping_definition = EXAMPLE_MAPPING
        # This schema shares the field names `id` and `name` with
        # EXAMPLE_SCHEMA. The field types differ though, so we should expect a
        # validation error to occur during entity extraction.
        error_count = 2
        schema = {
            'type': 'record',
            'name': 'Test',
            'fields': [
                {
                    'name': 'id',
                    'type': 'int',  # error 1
                },
                {
                    'name': 'name',  # error 2
                    'type': {
                        'type': 'enum',
                        'name': 'Name',
                        'symbols': ['John', 'Jane'],
                    }
                },
            ]
        }
        schemas = {'Person': schema}
        submission_data, entities = entity_extractor.extract_create_entities(
            submission_payload,
            mapping_definition,
            schemas,
        )
        submission_errors = submission_data['aether_errors']
        self.assertEqual(
            len(submission_errors),
            len(EXAMPLE_SOURCE_DATA['data']['people']) * error_count,
        )
        self.assertEqual(len(entities), 0)

    def test_extract_create_entities__error_not_a_uuid(self):
        submission_payload = {'id': 'not-a-uuid', 'a': 1}
        mapping_definition = {
            'entities': {'Test': str(uuid.uuid4())},
            'mapping': [
                ['$.id', 'Test.id'],
                ['$.a', 'Test.b'],
            ],
        }
        schema = {
            'type': 'record',
            'name': 'Test',
            'fields': [
                {
                    'name': 'id',
                    'type': 'string',
                },
                {
                    'name': 'b',
                    'type': 'int',
                },
            ],
        }
        schemas = {'Test': schema}
        submission_data, entities = entity_extractor.extract_create_entities(
            submission_payload,
            mapping_definition,
            schemas,
        )
        submission_errors = submission_data['aether_errors']
        self.assertEqual(len(entities), 0)
        self.assertEqual(len(submission_errors), 1)
        self.assertIn('is not a valid uuid',
                      submission_errors[0]['description'])

    def test_is_not_custom_jsonpath(self):
        # Examples taken from https://github.com/json-path/JsonPath#path-examples
        example_paths = [
            '$.store.book[*].author',
            '$..author',
            '$.store.*',
            '$.store..price',
            '$..book[2]',
            '$..book[-2]',
            '$..book[0,1]',
            '$..book[:2]',
            '$..book[1:2]',
            '$..book[-2:]',
            '$..book[2:]',
            '$..book[?(@.isbn)]',
            '$.store.book[?(@.price < 10)]',
            '$..book[?(@.price <= $["expensive"])]'
            '$..book[?(@.author =~ /.*REES/i)]'
            '$..*',
            '$..book.length()',
        ]
        for path in example_paths:
            result = entity_extractor.CUSTOM_JSONPATH_WILDCARD_REGEX.match(path)
            self.assertIsNone(result)

    def test_find_by_jsonpath__filter_by_prefix(self):
        obj = {
            'dose-1': {
                'id': 1,
            },
            'dose-2': {
                'id': 2,
            },
            'person-1': {
                'id': 3,
            },
        }
        expected = set([1, 2])
        path = '$.dose-*.id'
        result = set([x.value for x in entity_extractor.find_by_jsonpath(obj, path)])
        self.assertEqual(expected, result)

    def test_find_by_jsonpath__filter_by_prefix_nested_base(self):
        obj = {
            'data': {
                'dose-1': {
                    'id': 1,
                },
                'dose-2': {
                    'id': 2,
                },
                'person-1': {
                    'id': 3,
                },
            }
        }
        expected = set([1, 2])
        path = '$.data.dose-*.id'
        result = set([x.value for x in entity_extractor.find_by_jsonpath(obj, path)])
        self.assertEqual(expected, result)

    def test_find_by_jsonpath__nested(self):
        obj = {
            'dose-1': {
                'id': 1,
            },
            'dose-2': {
                'id': 2,
            },
            'person-1': {
                'id': 3,
                'household': {
                    'id': 4,
                },
            },
        }
        expected = set([4])
        path = '$.person-*.household.id'
        result = set([x.value for x in entity_extractor.find_by_jsonpath(obj, path)])
        self.assertEqual(expected, result)

    def test_find_by_jsonpath__fallback_to_jsonpath_ng(self):
        obj = {
            'dose-1': {
                'id': 1,
            },
            'dose-2': {
                'id': 2,
            },
            'person-1': {
                'id': 3,
            },
        }
        expected = set([1, 2, 3])
        path = '$.*.id'
        result = set([x.value for x in entity_extractor.find_by_jsonpath(obj, path)])
        self.assertEqual(expected, result)

    def test_find_by_jsonpath__fallback_array(self):
        obj = {
            'households': [
                {
                    'id': 1,
                },
                {
                    'id': 2,
                },
                {
                    'id': 3,
                },
            ]
        }
        expected = set([1, 2, 3])
        path = '$.households[*].id'
        result = set([x.value for x in entity_extractor.find_by_jsonpath(obj, path)])
        self.assertEqual(expected, result)
