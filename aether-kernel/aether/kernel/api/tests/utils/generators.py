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

import random

from ddf import G, M

from django.core.files.uploadedfile import SimpleUploadedFile

from aether.python.avro.tools import random_avro
from aether.kernel.api import models
from aether.kernel.api.entity_extractor import run_extraction

MAPPINGS_COUNT_RANGE = (1, 3)
SUBMISSIONS_COUNT_RANGE = (2, 3)
ATTACHMENTS_COUNT_RANGE = (1, 2)


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


def mappingset_schema():
    return {
        'name': 'Test',
        'type': 'record',
        'fields': [
            {
                'name': 'test_field',
                'type': 'string',
            },
        ],
    }


def mapping_definition(entity_test_pk):
    return {
        'entities': {'Test': str(entity_test_pk)},
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
        schema_field_values=None,
        schemadecorator_field_values=None,
        mappingset_field_values=None,
        mapping_field_values=None,
        submission_field_values=None,
        include_attachments=False,
):
    '''
    Generate an Aether Project.

    This function can be used in unit tests to generate instances of all kernel
    models.

    If necessary, the default field values of a model can be overridden,
    using either static values:

    >>> generate_project(project_field_values={'name': 'A Project Name'})

    or generators:

    >>> import random
    >>> names = lambda x: random.choice(['a', 'b', 'c'])
    >>> generate_project(project_field_values={'name': names})
    '''

    project = G(
        models.Project,
        **get_field_values(
            default=dict(),
            values=project_field_values,
        ),
    )

    schema = G(
        models.Schema,
        **get_field_values(
            default=dict(
                definition=schema_definition(),
            ),
            values=schema_field_values,
        ),
    )

    schemadecorator = G(
        model=models.SchemaDecorator,
        **get_field_values(
            default=dict(
                project=project,
                schema=schema,
            ),
            values=schemadecorator_field_values,
        ),
    )

    for _ in range(random.randint(*MAPPINGS_COUNT_RANGE)):
        mappingset = G(
            models.MappingSet,
            **get_field_values(
                default=dict(
                    project=project,
                    schema=mappingset_schema(),
                ),
                values=mappingset_field_values,
            ),
        )

        # create a random input based on the schema
        if not mappingset.input and mappingset.schema:
            mappingset.input = random_avro(mappingset.schema)
            mappingset.save()

        models.Mapping.objects.create(
            **get_field_values(
                default=dict(
                    name=mappingset.name,
                    mappingset=mappingset,
                    definition=mapping_definition(schemadecorator.pk),
                ),
                values=mapping_field_values,
            ),
        )

        for _ in range(random.randint(*SUBMISSIONS_COUNT_RANGE)):
            submission = G(
                models.Submission,
                **get_field_values(
                    default=dict(
                        # use mappingset schema to generate random payloads
                        payload=random_avro(mappingset.schema),
                        project=project,
                        mappingset=mappingset,
                    ),
                    values=submission_field_values,
                ),
            )

            if include_attachments:
                for index in range(random.randint(*ATTACHMENTS_COUNT_RANGE)):
                    models.Attachment.objects.create(
                        submission=submission,
                        attachment_file=SimpleUploadedFile(f'sample_{index}.txt', b'abc'),
                    )

            # extract entities
            run_extraction(submission)

    return project, schema


def generate_random_string():
    return M('---------------------')
