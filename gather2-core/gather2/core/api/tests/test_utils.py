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
        data = [{"dob": "2000-01-01", "name": "PersonA"}]
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
        expected = ['_id', '_rev', 'name', 'dob', 'villageID']
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
        entity_stubs = EXAMPLE_ENTITY_DEFINITION
        expected_entity = EXAMPLE_ENTITY
        data, entities = utils.extract_entity(requirements, response_data, entity_stubs)
        self.assertEquals(len(expected_entity['Person']), len(entities['Person']))
