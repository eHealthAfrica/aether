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

import uuid

from django.test import TestCase

from aether.kernel.api.models import Project, Schema, SchemaDecorator, Mapping, MappingSet
from aether.kernel.api.project_artefacts import (
    get_project_artefacts as retrieve,
    upsert_project_artefacts as generate,
    upsert_project_with_avro_schemas as generate_from_avro,
    __upsert_instance as upsert,
)


class ProjectArtefactsTests(TestCase):

    def test__upsert_item(self):
        # creates it with no id
        project_0 = upsert(Project, pk=None, ignore_fields=[], name='Project None', unknown=2)

        self.assertIsNotNone(project_0)
        self.assertIsNotNone(project_0.pk)
        self.assertEqual(project_0.name, 'Project None')

        _id = uuid.uuid4()

        # creates it with id
        project_1 = upsert(Project, pk=str(_id), ignore_fields=['revision'],
                           name='Project test', revision='2')

        self.assertIsNotNone(project_1)
        self.assertEqual(project_1.pk, _id)
        self.assertEqual(project_1.name, 'Project test')
        self.assertEqual(project_1.revision, '2', 'accepts revision value if creates the object')

        # updates it
        project_2 = upsert(Project, pk=_id, ignore_fields=['revision'],
                           name='Project test 2', revision='Z')

        self.assertIsNotNone(project_2)
        self.assertEqual(project_2.pk, _id)
        self.assertEqual(project_2.name, 'Project test 2')
        self.assertEqual(project_2.revision, '2', 'ignores new revision value if updates the object')

        # creates with foreign keys
        mappingset_0 = upsert(MappingSet, pk=None, ignore_fields=[],
                              name='Mappingset None', project=project_1, input={})

        self.assertIsNotNone(mappingset_0)
        self.assertIsNotNone(mappingset_0.pk)
        self.assertEqual(mappingset_0.name, 'Mappingset None')
        self.assertEqual(mappingset_0.project, project_2)

        # updates indicated fields, keeps the rest
        mappingset_1 = upsert(MappingSet, pk=mappingset_0.pk, ignore_fields=['name'],
                              unknown=True)

        self.assertEqual(mappingset_1.pk, mappingset_0.pk)
        self.assertEqual(mappingset_1.name, 'Mappingset None')
        self.assertEqual(mappingset_1.project, project_1)

        # does not update with action 'create'
        mappingset_2 = upsert(MappingSet, pk=mappingset_0.pk, ignore_fields=[], action='create',
                              name='Mappingset Two', project=project_1)

        self.assertEqual(mappingset_2.pk, mappingset_0.pk)
        self.assertEqual(mappingset_2.name, 'Mappingset None')
        self.assertEqual(mappingset_2.project, project_2)

    def test__upsert_project_artefacts__project(self):

        # creates the project if there is no project with that id
        project_id = str(uuid.uuid4())
        self.assertEqual(Project.objects.filter(pk=project_id).count(), 0)

        results = generate(project_id=project_id)

        self.assertEqual(results['project'], str(project_id))
        self.assertEqual(results['schemas'], set())
        self.assertEqual(results['schema_decorators'], set())
        self.assertEqual(results['mappingsets'], set())

        new_project = Project.objects.get(pk=project_id)
        self.assertIsNotNone(new_project.name)

        # creates the project if no id indicated
        results = generate(project_name='New project')

        self.assertIsNotNone(results['project'])
        self.assertEqual(results['schemas'], set())
        self.assertEqual(results['schema_decorators'], set())
        self.assertEqual(results['mappings'], set())

        project = Project.objects.get(pk=results['project'])
        self.assertEqual(project.name, 'New project')

        results_retrieve = retrieve(project=project)
        self.assertEqual(results, results_retrieve)

        results = generate(project_id=project.pk, project_name='Something new')

        project.refresh_from_db()
        self.assertEqual(results['project'], str(project.pk))
        self.assertEqual(results['schemas'], set())
        self.assertEqual(results['schema_decorators'], set())
        self.assertEqual(results['mappings'], set())
        self.assertEqual(project.name, 'New project', 'name is not updated')

    def test__upsert_project_artefacts__schemas(self):
        project = Project.objects.create(name='Project')
        schema_id = str(uuid.uuid4())

        results_1 = generate(project_id=project.pk, project_name=project.name, schemas=[
            {'id': schema_id, 'name': 'Schema', 'definition': {}},
        ])
        results_retrieve = retrieve(project=project)
        self.assertEqual(results_1, results_retrieve)

        self.assertEqual(results_1['project'], str(project.pk))
        self.assertEqual(results_1['schemas'], set([schema_id]))
        self.assertEqual(results_1['schema_decorators'], set([schema_id]),
                         'Schema decorators inherit schema ids')
        self.assertEqual(results_1['mappings'], set())

        schema_decorator_id = list(results_1['schema_decorators'])[0]

        schema = Schema.objects.get(pk=schema_id)
        self.assertEqual(schema.name, 'Schema')
        self.assertEqual(schema.revision, '1')
        self.assertEqual(schema.definition, {})
        self.assertEqual(schema.type, 'org.ehealthafrica.aether')
        self.assertIsNone(schema.family)

        schema_decorator = SchemaDecorator.objects.get(pk=schema_decorator_id)
        self.assertEqual(schema_decorator.project, project)
        self.assertEqual(schema_decorator.schema, schema)

        results_2 = generate(project_id=project.pk, project_name=project.name, schemas=[
            # in this case nothing changes
            {'id': schema_id, 'name': 'Schema 2'},
        ])
        self.assertEqual(results_1, results_2, 'it does no generate a new schema decorator')

        schema.refresh_from_db()
        self.assertEqual(schema.name, 'Schema')
        self.assertEqual(schema.revision, '1')
        self.assertEqual(schema.definition, {})
        self.assertEqual(schema.type, 'org.ehealthafrica.aether')
        self.assertIsNone(schema.family)

        # delete schema decorator
        schema_decorator.delete()
        results_3 = generate(project_id=project.pk, project_name=project.name, schemas=[
            # in this case the definition is updated and the deleted schema decorator re-generated
            {'id': schema_id, 'definition': {'name': 'Schema'}, 'type': 't', 'family': 'f'},
        ])
        self.assertEqual(results_1, results_3, 'generates a new schema decorator with the schema id')
        self.assertEqual(results_3['project'], str(project.pk))
        self.assertEqual(results_3['schemas'], set([schema_id]))
        self.assertEqual(len(results_3['schema_decorators']), 1)
        self.assertEqual(results_3['mappings'], set())

        schema.refresh_from_db()
        self.assertEqual(schema.name, 'Schema')
        self.assertEqual(schema.revision, '1')
        self.assertEqual(schema.definition, {'name': 'Schema'})
        self.assertEqual(schema.type, 't')
        self.assertEqual(schema.family, 'f')

        # creating a new empt schema
        results_4 = generate(project_id=project.pk, project_name=project.name, schemas=[
            # It's possible to create empty schemas!!!
            {},
        ])
        self.assertNotEqual(results_1, results_4, 'only returns the affected ids')
        self.assertEqual(len(results_1['schemas']), 1)
        self.assertEqual(len(results_1['schema_decorators']), 1)

        results_retrieve = retrieve(project=project)
        self.assertNotEqual(results_4, results_retrieve,
                            'only returns the affected ids NEVER ALL OF THEM')

    def test__upsert_project_artefacts__mappings(self):
        project = Project.objects.create(name='Project')
        mapping_id = str(uuid.uuid4())

        results_1 = generate(
            project_id=project.pk,
            project_name=project.name,
            mappings=[
                {'id': mapping_id, 'name': 'Mapping'},
            ],
        )
        results_retrieve = retrieve(project=project)
        self.assertEqual(results_1, results_retrieve)

        self.assertEqual(results_1['project'], str(project.pk))
        self.assertEqual(results_1['schemas'], set())
        self.assertEqual(results_1['schema_decorators'], set())
        self.assertEqual(results_1['mappingsets'], set([mapping_id]))
        self.assertEqual(results_1['mappings'], set([mapping_id]))

        mapping = Mapping.objects.get(pk=mapping_id)
        self.assertEqual(mapping.name, 'Mapping')
        self.assertEqual(mapping.revision, '1')
        self.assertEqual(mapping.definition, {'mapping': [], 'entities': {}})

        # the method has also created the missing mappingset
        mappingset = MappingSet.objects.get(pk=mapping_id)
        self.assertEqual(mappingset.name, 'Mapping')
        self.assertEqual(mappingset.revision, '1')
        self.assertEqual(mappingset.input, {})

        results_2 = generate(
            project_id=project.pk,
            project_name=project.name,
            mappingsets=[
                # in this case nothing changes
                {'id': mapping_id, 'name': 'Mapping Set 2'}
            ],
            mappings=[
                # in this case nothing changes
                {'id': mapping_id, 'name': 'Mapping 2'},
            ],
        )
        self.assertEqual(results_1, results_2)

        mapping.refresh_from_db()
        self.assertEqual(mapping.name, 'Mapping')
        self.assertEqual(mapping.revision, '1')
        self.assertEqual(mapping.definition, {'mapping': [], 'entities': {}})

        mappingset.refresh_from_db()
        self.assertEqual(mappingset.name, 'Mapping')
        self.assertEqual(mappingset.input, {})

        results_3 = generate(
            project_id=project.pk,
            project_name=project.name,
            mappingsets=[
                {
                    'id': mapping_id,
                    'name': 'Mapping Set 2',
                    'schema': {
                        'name': 'Name',
                        'type': 'record',
                        'fields': [
                            {'name': 'name', 'type': 'string'},
                        ],
                    },
                    'input': {'name': 'a'},
                }
            ],
            mappings=[
                # in this case the definition is updated and the given input ignored
                {'id': mapping_id, 'definition': {}, 'input': {'name': 'b'}},
            ],
        )
        self.assertEqual(results_1, results_3)

        mapping.refresh_from_db()
        self.assertEqual(mapping.name, 'Mapping')
        self.assertEqual(mapping.revision, '1')
        self.assertEqual(mapping.definition, {'mapping': [], 'entities': {}})

        mappingset.refresh_from_db()
        self.assertEqual(mappingset.schema, {
            'name': 'Name',
            'type': 'record',
            'fields': [
                {'name': 'name', 'type': 'string'},
            ],
        })
        self.assertEqual(mappingset.input, {'name': 'a'})

        # creating a new empty mapping
        results_4 = generate(
            project_id=project.pk,
            project_name=project.name,
            mappings=[
                # It's possible to create empty mappings!!!
                {},
            ]
        )
        self.assertNotEqual(results_1, results_4, 'only returns the affected ids')
        self.assertEqual(len(results_1['mappings']), 1)

        results_retrieve = retrieve(project=project)
        self.assertNotEqual(results_4, results_retrieve,
                            'only returns the affected ids NEVER ALL OF THEM')

        # mapping with rules indicating the entities
        generate(
            project_id=project.pk,
            project_name=project.name,
            schemas=[
                {'name': 'Person', 'definition': {}},
                {'name': 'Contact', 'definition': {}},
            ],
            mappings=[
                {
                    'id': mapping_id,
                    'definition': {
                        'mapping': [
                            ['$.id', 'Person.id'],
                            ['$.name', 'Person.name'],
                            ['$.id', 'Contact.id'],
                        ],
                        'entities': {}
                    }
                },
            ]
        )
        mapping.refresh_from_db()
        self.assertEqual(mapping.definition['entities'], {})

        # mapping with rules but without indicating the entities
        generate(
            project_id=project.pk,
            project_name=project.name,
            schemas=[
                {'name': 'Person', 'definition': {}},
                {'name': 'Contact', 'definition': {}},
            ],
            mappings=[
                {
                    'id': mapping_id,
                    'definition': {
                        'mapping': [
                            ['$.id', 'Person.id'],
                            ['$.name', 'Person.name'],
                            ['$.id', 'Contact.id'],
                        ]
                    }
                },
            ]
        )
        mapping.refresh_from_db()
        self.assertNotEqual(mapping.definition['entities'], {})
        self.assertIn('Person', mapping.definition['entities'])
        self.assertIn('Contact', mapping.definition['entities'])

    def test__upsert_project_artefacts__duplicated_name(self):
        SCHEMA_NAME = 'Schema'

        # create the first schema with that name
        Schema.objects.create(name=SCHEMA_NAME, definition={})

        schemas = []
        schema_ids = []
        for i in range(5):
            schema_id = str(uuid.uuid4())
            schemas.append({'id': schema_id, 'name': SCHEMA_NAME})
            schema_ids.append(schema_id)

        # try to generate 5 more schemas with the same name
        generate(schemas=schemas)

        for i in range(5):
            schema_id = schema_ids[i]
            schema = Schema.objects.get(pk=schema_id)
            # the new schemas have a numerical suffix
            self.assertEqual(schema.name, f'{SCHEMA_NAME}-{str(i + 1)}')

    def test__upsert_project_with_avro_schemas(self):
        self.assertEqual(Project.objects.count(), 0)
        self.assertEqual(Schema.objects.count(), 0)

        avro_schema = {
            'name': 'Person',
            'type': 'record',
            'fields': [
                {
                    'name': 'first_name',
                    'type': 'string',
                },
                {
                    'name': 'last_name',
                    'type': 'string',
                },
            ]
        }

        generate_from_avro(avro_schemas=[{'definition': avro_schema}], family='test')

        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Schema.objects.count(), 1)
        self.assertEqual(SchemaDecorator.objects.count(), 1)
        self.assertEqual(MappingSet.objects.count(), 1)
        self.assertEqual(Mapping.objects.count(), 1)

        schema = Schema.objects.first()
        self.assertEqual(schema.family, 'test')
        self.assertEqual(schema.type, 'org.ehealthafrica.aether')
        self.assertEqual(schema.definition, {
            'namespace': 'org.ehealthafrica.aether',
            'name': 'Person',
            'type': 'record',
            'fields': [
                {
                    'name': 'first_name',
                    'type': 'string',
                },
                {
                    'name': 'last_name',
                    'type': 'string',
                },
                {
                    'doc': 'UUID',
                    'name': 'id',
                    'type': 'string',
                },
            ]
        })

        there_is_passthrough = False
        there_is_empty = False
        for mapping in Mapping.objects.all():
            if schema.id == mapping.id:
                # the passthrough mapping
                there_is_passthrough = True
                self.assertEqual(mapping.definition, {
                    'entities': {
                        'Person': str(schema.id),
                    },
                    'mapping': [
                        ['$.first_name', 'Person.first_name'],
                        ['$.last_name', 'Person.last_name'],
                        ['#!uuid', 'Person.id'],
                    ]
                })
            else:
                # the empty mapping
                there_is_empty = True
                self.assertEqual(mapping.definition, {'mapping': [], 'entities': {}})

        self.assertTrue(there_is_passthrough)
        self.assertFalse(there_is_empty)
