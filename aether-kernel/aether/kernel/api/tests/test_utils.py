from collections import namedtuple

from django.test import TestCase
from .. import utils
from . import (EXAMPLE_MAPPING, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA,
               EXAMPLE_REQUIREMENTS, EXAMPLE_ENTITY_DEFINITION,
               EXAMPLE_FIELD_MAPPINGS, EXAMPLE_ENTITY)


class UtilsTests(TestCase):

    def test_json_prettified_simple(self):
        data = {}
        expected = '<pre><span></span><span class="p">{}</span>\n</pre>'
        pretty = str(utils.json_prettified(data))
        self.assertTrue(expected in pretty, pretty)

    def test_code_prettified_simple(self):
        data = 'print "Hello world!"'
        expected = '<span class="s2">&quot;Hello world!&quot;</span>'

        pretty = str(utils.code_prettified(data))
        self.assertTrue(expected in pretty, pretty)

    def test_json_printable(self):
        data = [{'dob': '2000-01-01', 'name': 'PersonA'}]
        expected = [{'dob': '2000-01-01', 'name': 'PersonA'}]
        printable = utils.json_printable(data)
        self.assertEquals(printable, expected)

    def test_json_printable_other_obj(self):
        data = 2
        expected = 2
        printable = utils.json_printable(data)
        self.assertEquals(printable, expected)

    def test_get_field_mappings(self):
        mapping = EXAMPLE_MAPPING
        expected = EXAMPLE_FIELD_MAPPINGS
        field_mapping = str(utils.get_field_mappings(mapping))
        self.assertTrue(str(expected) in field_mapping, field_mapping)

    def test_JSP_get_basic_fields(self):
        avro_obj = EXAMPLE_SCHEMA
        expected = ['id', '_rev', 'name', 'dob', 'villageID']
        basic_fields = str(utils.JSP_get_basic_fields(avro_obj))
        self.assertTrue(str(expected) in basic_fields, basic_fields)

    def test_get_entity_definitions(self):
        entity_type = 'Person'
        mapping = EXAMPLE_MAPPING
        schema = {entity_type: EXAMPLE_SCHEMA}
        expected = EXAMPLE_ENTITY_DEFINITION
        entity_definition = str(utils.get_entity_definitions(mapping, schema))
        self.assertTrue(str(expected) in entity_definition, entity_definition)

    def test_get_entity_requirements(self):
        entities = EXAMPLE_ENTITY_DEFINITION
        field_mappings = EXAMPLE_FIELD_MAPPINGS
        expected = EXAMPLE_REQUIREMENTS
        entity_requirements = str(utils.get_entity_requirements(entities, field_mappings))
        self.assertTrue(str(expected) in entity_requirements, entity_requirements)

    def test_get_entity_stub(self):
        requirements = EXAMPLE_REQUIREMENTS
        source_data = EXAMPLE_SOURCE_DATA
        entity_definitions = EXAMPLE_ENTITY_DEFINITION
        entity_name = 'Person'
        stub = utils.get_entity_stub(requirements, entity_definitions, entity_name, source_data)
        self.assertEquals(len(stub.get('dob')), 3)

    def test_resolve_source_reference__single_resolution(self):
        data = EXAMPLE_SOURCE_DATA
        requirements = EXAMPLE_REQUIREMENTS
        entities = EXAMPLE_ENTITY
        entity_name = 'Person'
        field = 'villageID'
        path = requirements.get(entity_name, {}).get(field)[0]
        resolved_count = utils.resolve_source_reference(path, entities, entity_name, 0, field, data)
        self.assertEquals(resolved_count, 1)

    def test_resolve_source_reference__multiple_resolutions(self):
        data = EXAMPLE_SOURCE_DATA
        requirements = EXAMPLE_REQUIREMENTS
        entities = EXAMPLE_ENTITY
        entity_name = 'Person'
        field = 'dob'
        path = requirements.get(entity_name, {}).get(field)[0]
        resolved_count = utils.resolve_source_reference(path, entities, entity_name, 0, field, data)
        self.assertEquals(resolved_count, 3)

    def test_get_or_make_uuid(self):
        entity_type = 'Person'
        field_name = '_id'
        instance_number = 0
        source_data = EXAMPLE_SOURCE_DATA
        uuid = str(utils.get_or_make_uuid(entity_type, field_name, instance_number, source_data))
        self.assertEquals(uuid.count('-'), 4)

    def test_extract_entity(self):
        requirements = EXAMPLE_REQUIREMENTS
        response_data = EXAMPLE_SOURCE_DATA
        entity_definitions = EXAMPLE_ENTITY_DEFINITION
        expected_entity = EXAMPLE_ENTITY
        entities = {'Person': []}
        entity_name = 'Person'
        entity_stub = utils.get_entity_stub(
            requirements, entity_definitions, entity_name, response_data
        )
        failed_actions = utils.extract_entity(
            entity_name, entities, requirements, response_data, entity_stub
        )
        self.assertEquals(len(expected_entity['Person']), len(entities['Person']))
        self.assertEquals(len(failed_actions), 0)

    def test_extract_entities(self):
        requirements = EXAMPLE_REQUIREMENTS
        response_data = EXAMPLE_SOURCE_DATA
        entity_stubs = EXAMPLE_ENTITY_DEFINITION
        expected_entity = EXAMPLE_ENTITY
        data, entities = utils.extract_entities(requirements, response_data, entity_stubs)
        self.assertEquals(len(expected_entity['Person']), len(entities['Person']))

    # def test_extract_create_entities(self):
    #     import pdb; pdb.set_trace()

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
            result = utils.custom_jsonpath_wildcard_regex.match(path)
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
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)

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
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)

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
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)

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
        result = set([x.value for x in utils.find_by_jsonpath(obj, path)])
        self.assertEquals(expected, result)
