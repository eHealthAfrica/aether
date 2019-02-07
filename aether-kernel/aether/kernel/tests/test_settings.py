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

from django.conf import settings
from django.test import TestCase


class SettingsTest(TestCase):

    def test_default_variables(self):

        self.assertTrue(settings.TESTING)
        self.assertFalse(settings.DEBUG)

        self.assertEqual(settings.ROOT_URLCONF, 'aether.kernel.urls')
        self.assertEqual(settings.APP_NAME, 'Aether Kernel')

        self.assertEqual(settings.EXPORT_CSV_ESCAPE, '\\')
        self.assertEqual(settings.EXPORT_CSV_QUOTE, '"')
        self.assertEqual(settings.EXPORT_CSV_SEPARATOR, ',')
        self.assertEqual(settings.EXPORT_DATA_FORMAT, 'split')
        self.assertEqual(settings.EXPORT_HEADER_CONTENT, 'labels')
        self.assertEqual(settings.EXPORT_HEADER_SEPARATOR, '/')
        self.assertEqual(settings.EXPORT_HEADER_SHORTEN, 'no')
