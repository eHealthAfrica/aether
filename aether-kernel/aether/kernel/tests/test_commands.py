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

from unittest import mock
import os

from django.core.management import call_command
from django.test import TestCase

from aether.kernel.api.tests.utils.generators import generate_project
from aether.kernel.api.models import Entity


class ExtractEntitiesCommandTest(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    @mock.patch('aether.kernel.management.commands.extract_entities.run_extraction')
    def test__extract_entities__no_data(self, mock_extractor):
        try:
            call_command('extract_entities', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        mock_extractor.assert_not_called()

    def test__extract_entities__success(self):
        generate_project()
        self.assertNotEqual(Entity.objects.count(), 0)

        entities = Entity.objects.count()
        try:
            call_command('extract_entities', stdout=self.out, stderr=self.out)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
        self.assertEqual(Entity.objects.count(), entities)

    def test__extract_entities__error(self):
        generate_project()
        self.assertNotEqual(Entity.objects.count(), 0)
        entities_count = Entity.objects.count()

        with mock.patch('aether.kernel.api.entity_extractor.extract_create_entities',
                        side_effect=Exception('oops')) as mock_extractor:
            try:
                call_command('extract_entities', stdout=self.out, stderr=self.out)
                self.assertTrue(True)
            except Exception:
                self.assertTrue(False)

        self.assertEqual(Entity.objects.count(), entities_count,
                         'transaction atomic reverts the deletion')
        mock_extractor.assert_called()
