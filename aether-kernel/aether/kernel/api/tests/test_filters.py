# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from aether.python.entity.extractor import ENTITY_EXTRACTION_ERRORS, ENTITY_EXTRACTION_ENRICHMENT

from aether.kernel.api import models
from aether.kernel.api.filters import EntityFilter, SubmissionFilter
from aether.kernel.api.tests.utils.generators import (
    generate_project,
    generate_random_string,
)

ENTITY_EXTRACTION_FIELDS = [
    ENTITY_EXTRACTION_ERRORS,
    ENTITY_EXTRACTION_ENRICHMENT,
]


@override_settings(MULTITENANCY=False)
class TestFilters(TestCase):

    def setUp(self):
        username = 'user'
        email = 'user@example.com'
        password = 'password'
        self.user = get_user_model().objects.create_user(username, email, password)
        self.assertTrue(self.client.login(username=username, password=password))

    def test_project_filter__active(self):
        url = reverse(viewname='project-list')
        # Generate projects.
        for _ in range(random.randint(2, 4)):
            generate_project(project_field_values={'active': True})
        for _ in range(random.randint(2, 4)):
            generate_project(project_field_values={'active': False})

        # active
        active_count = models.Project.objects.filter(active=True).count()
        self.assertTrue(active_count > 0)
        kwargs = {'active': True, 'fields': 'id'}
        response = self.client.get(url, kwargs).json()
        self.assertEqual(response['count'], active_count)

        # inactive
        inactive_count = models.Project.objects.filter(active=False).count()
        self.assertTrue(inactive_count > 0)
        kwargs = {'active': False, 'fields': 'id'}
        response = self.client.get(url, kwargs).json()
        self.assertEqual(response['count'], inactive_count)

    def test_schemadecorator_filter__active(self):
        url = reverse(viewname='schemadecorator-list')
        # Generate projects.
        for _ in range(random.randint(2, 4)):
            generate_project(project_field_values={'active': True})
        for _ in range(random.randint(2, 4)):
            generate_project(project_field_values={'active': False})

        sd_count = models.SchemaDecorator.objects.count()

        # active
        active_count = models.SchemaDecorator.objects.filter(project__active=True).count()
        self.assertTrue(0 < active_count and active_count < sd_count)
        kwargs = {'active': '1', 'fields': 'id', 'page_size': sd_count}
        response = self.client.get(url, kwargs).json()
        self.assertEqual(response['count'], active_count)

        # inactive
        inactive_count = models.SchemaDecorator.objects.filter(project__active=False).count()
        self.assertTrue(0 < inactive_count and inactive_count < sd_count)
        kwargs = {'active': False, 'fields': 'id', 'page_size': sd_count}
        response = self.client.get(url, kwargs).json()
        self.assertEqual(response['count'], inactive_count)

    def test_entity_filter__active(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(2, 4)):
            generate_project(project_field_values={'active': True})
        for _ in range(random.randint(2, 4)):
            generate_project(project_field_values={'active': False})

        entities_count = models.Entity.objects.count()

        # active
        active_count = models.Entity.objects.filter(project__active=True).count()
        self.assertTrue(active_count > 0)
        kwargs = {'active': True, 'fields': 'id', 'page_size': entities_count}
        response = self.client.get(url, kwargs).json()
        self.assertEqual(response['count'], active_count)

        # inactive
        inactive_count = models.Entity.objects.filter(project__active=False).count()
        self.assertTrue(inactive_count > 0)
        kwargs = {'active': False, 'fields': 'id', 'page_size': entities_count}
        response = self.client.get(url, kwargs).json()
        self.assertEqual(response['count'], inactive_count)

    def test_project_filter__by_schema(self):
        url = reverse(viewname='project-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        projects_count = models.Project.objects.count()
        # Get a list of all schemas.
        for schema in models.Schema.objects.all():
            # Request a list of all projects, filtered by `schema`.
            # This checks that ProjectFilter.schema exists and that
            # ProjectFilter has been correctly configured.
            expected = set([str(ps.project.id) for ps in schema.schemadecorators.all()])

            # by id
            kwargs = {'schema': str(schema.id), 'fields': 'id', 'page_size': projects_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'schema': schema.name, 'fields': 'id', 'page_size': projects_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_schema_filter__by_project(self):
        url = reverse(viewname='schema-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        schemas_count = models.Schema.objects.count()
        # Get a list of all projects.
        for project in models.Project.objects.all():
            # Request a list of all schemas, filtered by `project`.
            # This checks that SchemaFilter.project exists and that
            # SchemaFilter has been correctly configured.
            expected = set([str(ps.schema.id) for ps in project.schemadecorators.all()])

            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': schemas_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': schemas_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_schema_filter__by_mapping(self):
        url = reverse(viewname='schema-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        mappings_count = models.Mapping.objects.count()
        # Get a list of all mappings.
        for mapping in models.Mapping.objects.all():
            expected = set([str(ps.schema.id) for ps in mapping.schemadecorators.all()])
            # by id
            kwargs = {'mapping': str(mapping.id), 'fields': 'id', 'page_size': mappings_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'mapping': mapping.name, 'fields': 'id', 'page_size': mappings_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_entity_filter__by_project(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        entities_count = models.Entity.objects.count()
        # Get a list of all projects.
        for project in models.Project.objects.all():
            # Request a list of all entities, filtered by `project`.
            # This checks that EntityFilter.project exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in project.entities.all()])

            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': entities_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': entities_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_entity_filter__by_mapping(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        entities_count = models.Entity.objects.count()
        # Get a list of all mappings.
        for mapping in models.Mapping.objects.all():
            # Request a list of all entities, filtered by `mapping`.
            # This checks that EntityFilter.mapping exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in mapping.entities.all()])

            # by id
            kwargs = {'mapping': str(mapping.id), 'fields': 'id', 'page_size': entities_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'mapping': mapping.name, 'fields': 'id', 'page_size': entities_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_entity_filter__by_schema(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        entities_count = models.Entity.objects.count()
        # Get a list of all schemas.
        for schema in models.Schema.objects.all():
            # Request a list of all entities, filtered by `schema`.
            # This checks that EntityFilter.schema exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in schema.entities.all()])

            # by id
            kwargs = {'schema': str(schema.id), 'fields': 'id', 'page_size': entities_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'schema': schema.name, 'fields': 'id', 'page_size': entities_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_entity_filter__by_submission(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        entities_count = models.Entity.objects.count()
        # Get a list of all submissions.
        for submission in models.Submission.objects.all():
            # Request a list of all entities, filtered by `submission`.
            # This checks that EntityFilter.submission exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in submission.entities.all()])

            kwargs = {'submission': str(submission.id), 'fields': 'id', 'page_size': entities_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result, 'by submission')

    def test_entity_filter__by_family(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project(schema_field_values={
                'family': generate_random_string(),
            })
        entities_count = models.Entity.objects.count()
        # Get a list of all schema families.
        for family in models.Schema.objects.exclude(family=None).values_list('family', flat=True).distinct():
            self.assertIsNotNone(family)

            # Request a list of all entities, filtered by `family`.
            # This checks that EntityFilter.family exists and that
            # EntityFilter has been correctly configured.
            expected = set([str(e.id) for e in models.Entity.objects.filter(schemadecorator__schema__family=family)])

            # by family
            kwargs = {'family': family, 'fields': 'id', 'page_size': entities_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by family')

    def test_entity_filter__by_passthrough(self):
        url = reverse(viewname='entity-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        entities_count = models.Entity.objects.count()

        kwargs = {'passthrough': 'true', 'fields': 'id', 'page_size': entities_count}
        response = self.client.get(url, kwargs).json()
        self.assertEqual(response['count'], 0, 'there are no passthrough entities')

        # there are at least 5 schemas
        # Mark the first 3 as passthrough schemas
        expected = set()
        for schema in models.Schema.objects.all()[0:3]:
            schemadecorator = schema.schemadecorators.first()
            project = schemadecorator.project
            schema.family = str(project.pk)
            schema.save()

            mapping = schemadecorator.mappings.first()
            mapping.is_read_only = True  # one of the mappings is read only
            mapping.save()

            expected.update([str(e.id) for e in models.Entity.objects.filter(mapping=mapping)])

        self.assertNotEqual(len(expected), 0, 'there are passthrough entities')
        self.assertNotEqual(entities_count, len(expected), 'there are even more entities')
        response = self.client.get(url, kwargs).json()
        # Check both sets of ids for equality.
        self.assertEqual(response['count'], len(expected))
        result = set([r['id'] for r in response['results']])
        self.assertEqual(expected, result, 'by passthrough')

        # generating chaos
        # take one of the projects and assign all schema families with its pk
        project = models.Project.objects.last()
        expected = set()
        for schema in models.Schema.objects.all():
            schema.family = str(project.pk)
            schema.save()

            schemadecorator = schema.schemadecorators.first()
            own_project = schemadecorator.project
            if own_project == project:  # the only passthrough schema
                # take only one of the mappings
                mapping = schemadecorator.mappings.first()
                mapping.is_read_only = True  # one of the mappings is read only
                mapping.save()

                expected = set([str(e.id) for e in models.Entity.objects.filter(mapping=mapping)])

        self.assertNotEqual(len(expected), 0, 'there are passthrough entities')
        self.assertNotEqual(entities_count, len(expected), 'there are even more entities')

        response = self.client.get(url, kwargs).json()
        self.assertEqual(response['count'], len(expected))
        result = set([r['id'] for r in response['results']])
        self.assertEqual(expected, result, 'by passthrough')

        # by family
        kwargs = {'passthrough': 'false', 'family': str(project.pk), 'fields': 'id', 'page_size': entities_count}
        response = self.client.get(url, kwargs).json()
        # Check both sets of ids for equality.
        self.assertEqual(response['count'], entities_count, 'All entities belong to the same family')

    def test_entity_filter__by_date(self):
        for _ in range(random.randint(5, 10)):
            generate_project()
        count = models.Entity.objects.count()
        single = models.Entity.objects.first()
        entities = models.Entity.objects.all()
        for attr in ['created', 'modified']:
            single_value = getattr(single, attr)
            just_single = EntityFilter(data={f'{attr}': single_value}, queryset=entities)
            gt_single = EntityFilter(data={f'{attr}__gt': single_value}, queryset=entities)
            lt_single = EntityFilter(data={f'{attr}__lt': single_value}, queryset=entities)
            single_count = sum([1 for i in just_single.qs])
            gt_count = sum([1 for i in gt_single.qs])
            lt_count = sum([1 for i in lt_single.qs])
            self.assertEqual(single_count, 1)
            self.assertEqual(count, (single_count + gt_count + lt_count))

    def test_mapping_filter__by_mappingset(self):
        url = reverse(viewname='mapping-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        mappings_count = models.Mapping.objects.count()
        # Get a list of all mapping sets.
        for mappingset in models.MappingSet.objects.all():
            expected = set([str(e.id) for e in mappingset.mappings.all()])
            # by id
            kwargs = {'mappingset': str(mappingset.id), 'fields': 'id', 'page_size': mappings_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'mappingset': mappingset.name, 'fields': 'id', 'page_size': mappings_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_mapping_filter__by_schemadecorator(self):
        url = reverse(viewname='mapping-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        mappings_count = models.Mapping.objects.count()
        # Get a list of all schema decorators.
        for schemadecorator in models.SchemaDecorator.objects.all():
            expected = set([str(e.id) for e in schemadecorator.mappings.all()])
            # by id
            kwargs = {'schemadecorator': str(schemadecorator.id), 'fields': 'id', 'page_size': mappings_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'schemadecorator': schemadecorator.name, 'fields': 'id', 'page_size': mappings_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_schemadecorator_filter__by_mapping(self):
        url = reverse(viewname='schemadecorator-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        mappings_count = models.Mapping.objects.count()
        # Get a list of all mappings.
        for mapping in models.Mapping.objects.all():
            expected = set([str(ps.id) for ps in mapping.schemadecorators.all()])
            # by id
            kwargs = {'mapping': str(mapping.id), 'fields': 'id', 'page_size': mappings_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'mapping': mapping.name, 'fields': 'id', 'page_size': mappings_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_mappingset_filter__by_project(self):
        url = reverse(viewname='mappingset-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        mappingsets_count = models.MappingSet.objects.count()
        # Get a list of all projects.
        for project in models.Project.objects.all():
            expected = set([str(s.id) for s in project.mappingsets.all()])
            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': mappingsets_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': mappingsets_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

    def test_submission_filter__by_project(self):
        url = reverse(viewname='submission-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        submissions_count = models.Submission.objects.count()
        # Get a list of all projects.
        for project in models.Project.objects.all():
            # Request a list of all submissions, filtered by `project`.
            # This checks that SubmissionFilter.project exists and that
            # SubmissionFilter has been correctly configured.
            expected = set([str(s.id) for s in project.submissions.all()])

            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': submissions_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': submissions_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_submission_filter__by_mappingset(self):
        url = reverse(viewname='submission-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project()
        submissions_count = models.Submission.objects.count()
        # Get a list of all mapping sets.
        for mappingset in models.MappingSet.objects.all():
            # Request a list of all submissions, filtered by `mappingset`.
            # This checks that SubmissionFilter.mappingset exists and that
            # SubmissionFilter has been correctly configured.
            expected = set([str(e.id) for e in mappingset.submissions.all()])

            # by id
            kwargs = {'mappingset': str(mappingset.id), 'fields': 'id', 'page_size': submissions_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_id = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_id, 'by id')

            # by name
            kwargs = {'mappingset': mappingset.name, 'fields': 'id', 'page_size': submissions_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result_by_name = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result_by_name, 'by name')

    def test_submission_filter__by_date(self):
        for _ in range(random.randint(5, 10)):
            generate_project()
        count = models.Submission.objects.count()
        single = models.Submission.objects.first()
        submissions = models.Submission.objects.all()
        for attr in ['created', 'modified']:
            single_value = getattr(single, attr)
            just_single = SubmissionFilter(data={f'{attr}': single_value}, queryset=submissions)
            gt_single = SubmissionFilter(data={f'{attr}__gt': single_value}, queryset=submissions)
            lt_single = SubmissionFilter(data={f'{attr}__lt': single_value}, queryset=submissions)
            single_count = sum([1 for i in just_single.qs])
            gt_count = sum([1 for i in gt_single.qs])
            lt_count = sum([1 for i in lt_single.qs])
            self.assertEqual(single_count, 1)
            self.assertEqual(count, (single_count + gt_count + lt_count))

    def test_submission_filter__by_payload(self):
        url = reverse(viewname='submission-list')
        filters = [
            {'payload__a': '1'},
            {'payload__a__b': '"abcde"'},
            {'payload__a__b__c': '[1,2,3]'},
        ]
        payloads = [
            {'a': 1, 'z': 3},
            {'a': {'b': 'abcde'}, 'z': 3},
            {'a': {'b': {'c': [1, 2, 3]}}, 'z': 3}
        ]
        generate_project(submission_field_values={'payload': lambda x: random.choice(payloads)})
        submissions_count = models.Submission.objects.count()
        self.assertTrue(submissions_count > 0)

        filtered_submissions_count = 0
        for kwargs, payload in zip(filters, payloads):
            response = self.client.get(url, {
                'fields': 'payload',
                'page_size': submissions_count,
                **kwargs
            })
            submissions = response.json()
            filtered_submissions_count += submissions['count']
            for submission in submissions['results']:
                # remove aether_xxx entries in payload
                submission_payload = {
                    k: v
                    for k, v in submission['payload'].items()
                    if k not in ENTITY_EXTRACTION_FIELDS
                }
                original_payload = {
                    k: v
                    for k, v in payload.items()
                    if k not in ENTITY_EXTRACTION_FIELDS
                }
                self.assertEqual(submission_payload, original_payload)
        self.assertEqual(submissions_count, filtered_submissions_count)

    def test_submission_filter__by_payload__post(self):
        url = reverse(viewname='submission-query')
        filters = [
            {'payload__a': '1'},
            {'payload__a__b': '"abcde"'},
            {'payload__a__b__c': '[1,2,3]'},
        ]
        payloads = [
            {'a': 1, 'z': 3},
            {'a': {'b': 'abcde'}, 'z': 3},
            {'a': {'b': {'c': [1, 2, 3]}}, 'z': 3}
        ]
        generate_project(submission_field_values={'payload': lambda x: random.choice(payloads)})
        submissions_count = models.Submission.objects.count()
        self.assertTrue(submissions_count > 0)

        filtered_submissions_count = 0
        for kwargs, payload in zip(filters, payloads):
            response = self.client.post(f'{url}?fields=payload&page_size={submissions_count}', kwargs)
            submissions = response.json()
            filtered_submissions_count += submissions['count']
            for submission in submissions['results']:
                # remove aether_xxx entries in payload
                submission_payload = {
                    k: v
                    for k, v in submission['payload'].items()
                    if k not in ENTITY_EXTRACTION_FIELDS
                }
                original_payload = {
                    k: v
                    for k, v in payload.items()
                    if k not in ENTITY_EXTRACTION_FIELDS
                }
                self.assertEqual(submission_payload, original_payload)
        self.assertEqual(submissions_count, filtered_submissions_count)

    def test_submission_filter__by_payload__error(self):
        url = reverse(viewname='submission-list')
        generate_project(submission_field_values={'payload': {'a': '[1', 'z': 3}})
        submissions_count = models.Submission.objects.count()

        response = self.client.get(url, {
            'page_size': submissions_count,
            'payload__a': '[1',  # raise json.decoder.JSONDecodeError
        })
        self.assertEqual(response.json()['count'], submissions_count)

    def test_attachment_filter__by_project(self):
        url = reverse(viewname='attachment-list')
        # Generate projects.
        for _ in range(random.randint(5, 10)):
            generate_project(include_attachments=True)
        attachments_count = models.Attachment.objects.count()
        self.assertNotEqual(attachments_count, 0, ' There is at least one attachment')

        # Get a list of all projects.
        for project in models.Project.objects.all():
            expected = set([
                str(a.id)
                for a in models.Attachment.objects.filter(submission__project__pk=project.pk)
            ])
            # by id
            kwargs = {'project': str(project.id), 'fields': 'id', 'page_size': attachments_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)

            # by name
            kwargs = {'project': project.name, 'fields': 'id', 'page_size': attachments_count}
            response = self.client.get(url, kwargs).json()
            # Check both sets of ids for equality.
            self.assertEqual(response['count'], len(expected))
            result = set([r['id'] for r in response['results']])
            self.assertEqual(expected, result)
