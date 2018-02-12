from collections import namedtuple

from django.test import TestCase
from .. import mapping_validation
from .. import utils
from . import (EXAMPLE_MAPPING, EXAMPLE_SCHEMA, EXAMPLE_SOURCE_DATA,
               EXAMPLE_REQUIREMENTS, EXAMPLE_ENTITY_DEFINITION,
               EXAMPLE_FIELD_MAPPINGS, EXAMPLE_ENTITY)


class TestMappingValidation(TestCase):

    def test_validate_getter__success_1(self):
        submission_payload = {'a': {'b': 'x'}}
        path = '#!uuid'
        expected = mapping_validation.Success(path, [])
        result = mapping_validation.validate_getter(submission_payload, path)
        self.assertEquals(expected, result)

    def test_validate_getter__success_2(self):
        submission_payload = {'a': {'b': 'x'}}
        path = '$.a.b'
        expected = mapping_validation.Success(path, ['x'])
        result = mapping_validation.validate_getter(submission_payload, path)
        self.assertEquals(expected, result)

    def test_validate_getter__failure(self):
        submission_payload = {'a': {'b': 'x'}}
        path = '$.d.e'
        error_message = mapping_validation.MESSAGE_NO_MATCH
        expected = mapping_validation.Failure(path, error_message)
        result = mapping_validation.validate_getter(submission_payload, path)
        self.assertEquals(expected, result)

    def test_validate_setter__success(self):
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': 'x'}},
                projectschema_name='Test-1',
                status='Publishable',
            ),
            utils.Entity(
                id=2,
                payload={'c': {'d': 'y'}},
                projectschema_name='Test-2',
                status='Publishable',
            ),
        ]
        path = 'Test-1.a.b'
        expected = mapping_validation.Success(path, ['x'])
        result = mapping_validation.validate_setter(entity_list, path)
        self.assertEquals(expected, result)

    def test_validate_setter__failure(self):
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': 'x'}},
                projectschema_name='Test-1',
                status='Publishable',
            ),
            utils.Entity(
                id=2,
                payload={'c': {'d': 'y'}},
                projectschema_name='Test-2',
                status='Publishable',
            ),
        ]
        path = 'Test-3.a.b' # nonexistent project schema name "Test-3"
        error_message = mapping_validation.MESSAGE_NO_MATCH
        expected = mapping_validation.Failure(path, error_message)
        result = mapping_validation.validate_setter(entity_list, path)
        self.assertEquals(expected, result)

    def test_validate_mapping__success(self):
        submission_payload = {'a': {'b': 'x'}, 'c': {'d': 'y'}}
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': 'c'}},
                projectschema_name='Test-1',
                status='Publishable',
            ),
            utils.Entity(
                id=2,
                payload={'c': {'d': 'y'}},
                projectschema_name='Test-2',
                status='Publishable',
            ),
        ]
        mappings = [
            ('$.a.b', 'Test-1.a.b'),
            ('$.c.d', 'Test-2.c.d'),
        ]
        expected = []
        result = mapping_validation.validate_mappings(
            submission_payload, entity_list, mappings,
        )
        self.assertEquals(expected, result)

    def test_validate_mapping__success(self):
        submission_payload = {'a': {'b': 'x'}, 'c': {'d': 'y'}}
        entity_list = [
            utils.Entity(
                id=1,
                payload={'a': {'b': 'c'}},
                projectschema_name='Test-1',
                status='Publishable',
            ),
            utils.Entity(
                id=2,
                payload={'c': {'d': 'y'}},
                projectschema_name='Test-2',
                status='Publishable',
            ),
        ]
        mappings = [
            ('$.a.b', 'Test-1.nonexistent'),
            ('$.nonexistent', 'Test-2.c.d'),
        ]
        expected = [
            mapping_validation.Failure(
                path=mappings[0][1],
                error_message=mapping_validation.MESSAGE_NO_MATCH,
            ),
            mapping_validation.Failure(
                path=mappings[1][0],
                error_message=mapping_validation.MESSAGE_NO_MATCH,
            ),
        ]
        result = mapping_validation.validate_mappings(
            submission_payload, entity_list, mappings,
        )
        self.assertEquals(expected, result)
