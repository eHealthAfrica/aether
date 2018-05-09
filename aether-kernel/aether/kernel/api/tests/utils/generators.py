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

import random
import uuid

from autofixture import AutoFixture

from aether.kernel.api import models

ENTITIES_COUNT_RANGE = (10, 20)
SUBMISSIONS_COUNT_RANGE = (10, 20)


def schema_definition():
    return {
        'name': 'Test',
        'type': 'record',
        'fields': [
            {
                'name': 'id',
                'type': 'string',
            },
            {
                'name': 'test_field',
                'type': 'string',
            },
        ],
    }


def submission_payload():
    return {
        'test_field': 'test_value'
    }


def entity_payload():
    return {
        'id': str(uuid.uuid4()),
        'test_field': 'test_value',
    }


def mapping_definition():
    return {
        'entities': {'Test': 1},
        'mapping': [
            ['#!uuid', 'Test.id'],
            ['$.test_field', 'Test.test_field'],
        ],
    }


def get_field_values(default, values=None):
    '''
    Conditionally merge two dicts.
    '''
    if not values:
        return default
    return {**default, **values}


def generate_project(
        project_field_values=None,
        mapping_field_values=None,
        schema_field_values=None,
        projectschema_field_values=None,
        submission_field_values=None,
        entity_field_values=None,
):
    '''
    Generate an Aether Project.

    This function can be used in unit tests to generate instances of all kernel
    models. It wraps https://github.com/gregmuellegger/django-autofixture and
    provides an Aether-specific fixture generator.

    If necessary, the default field values of a model can be overridden,
    using either static values:

    >>> generate_project(project_field_values={'name': 'A Project Name'})

    or generators:

    >>> from autofixture import generators
    >>> names = generators.ChoicesGenerator(values=['a', 'b', 'c'])
    >>> generate_project(project_field_values={'name': names})
    '''

    project = AutoFixture(
        models.Project,
        field_values=get_field_values(
            default=dict(),
            values=project_field_values,
        ),
    ).create_one()
    mapping = AutoFixture(
        model=models.Mapping,
        field_values=get_field_values(
            default=dict(
                definition=mapping_definition(),
                project=project,
            ),
            values=mapping_field_values,
        ),
    ).create_one()
    schema = AutoFixture(
        model=models.Schema,
        field_values=get_field_values(
            default=dict(
                definition=schema_definition(),
            ),
            values=schema_field_values,
        ),
    ).create_one()
    projectschema = AutoFixture(
        model=models.ProjectSchema,
        field_values=get_field_values(
            default=dict(
                project=project,
                schema=schema,
            ),
            values=projectschema_field_values,
        ),
    ).create_one()
    AutoFixture(
        model=models.Submission,
        field_values=get_field_values(
            default=dict(
                revision=1,
                payload=submission_payload(),
                mapping=mapping,
                projectschema=projectschema,
            ),
            values=submission_field_values,
        ),
    ).create(random.randint(*SUBMISSIONS_COUNT_RANGE))
    AutoFixture(
        model=models.Entity,
        field_values=get_field_values(
            default=dict(
                revision=1,
                payload=entity_payload(),
                projectschema=projectschema,
            ),
            values=entity_field_values,
        ),
    ).create(random.randint(*ENTITIES_COUNT_RANGE))
