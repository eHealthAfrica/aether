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

from django.test import RequestFactory, override_settings

from . import CustomTestCase
from ..surveyors_utils import is_surveyor


@override_settings(MULTITENANCY=False)
class SurveyorsUtilsTests(CustomTestCase):

    def setUp(self):
        super(SurveyorsUtilsTests, self).setUp()

        self.request = RequestFactory().get('/')
        self.helper_create_superuser()
        self.helper_create_user()

    def test__project__surveyors(self):
        project = self.helper_create_project()
        self.assertEqual(project.surveyors.count(), 0, 'no granted surveyors')

        self.request.user = self.admin
        self.assertTrue(is_surveyor(self.request, project),
                        'superusers are always granted surveyors')

        self.request.user = self.user
        self.assertTrue(is_surveyor(self.request, project),
                        'if not granted surveyors all users are surveyors')

        surveyor = self.helper_create_surveyor()
        project.surveyors.add(surveyor)

        self.assertEqual(project.surveyors.count(), 1, 'one granted surveyor')
        self.request.user = surveyor
        self.assertTrue(is_surveyor(self.request, project))

        self.request.user = self.admin
        self.assertTrue(is_surveyor(self.request, project),
                        'superusers are always granted surveyors')

        self.request.user = self.user
        self.assertFalse(is_surveyor(self.request, project),
                         'if granted surveyors not all users are surveyors')

    def test__xform__surveyors(self):
        xform = self.helper_create_xform(with_media=True)
        media = xform.media_files.first()
        self.assertEqual(xform.surveyors.count(), 0, 'no granted surveyors')

        self.request.user = self.admin
        self.assertTrue(is_surveyor(self.request, xform),
                        'superusers are always granted surveyors')
        self.assertTrue(is_surveyor(self.request, media),
                        'superusers are always granted surveyors')

        self.request.user = self.user
        self.assertTrue(is_surveyor(self.request, xform),
                        'if not granted surveyors all users are surveyors')
        self.assertTrue(is_surveyor(self.request, media),
                        'if not granted surveyors all users are surveyors')

        surveyor = self.helper_create_surveyor(username='surveyor')
        xform.surveyors.add(surveyor)
        self.assertEqual(xform.surveyors.count(), 1, 'one custom granted surveyor')

        self.request.user = surveyor
        self.assertTrue(is_surveyor(self.request, xform))
        self.assertTrue(is_surveyor(self.request, media))

        self.request.user = self.admin
        self.assertTrue(is_surveyor(self.request, xform),
                        'superusers are always granted surveyors')
        self.assertTrue(is_surveyor(self.request, media),
                        'superusers are always granted surveyors')

        self.request.user = self.user
        self.assertFalse(is_surveyor(self.request, xform),
                         'if granted surveyors not all users are surveyors')
        self.assertFalse(is_surveyor(self.request, media),
                         'if granted surveyors not all users are surveyors')

        surveyor2 = self.helper_create_surveyor(username='surveyor2')
        xform.project.surveyors.add(surveyor2)
        self.assertEqual(xform.surveyors.count(), 1, 'one custom granted surveyor')

        self.request.user = surveyor
        self.assertTrue(is_surveyor(self.request, xform))
        self.assertTrue(is_surveyor(self.request, media))

        self.request.user = surveyor2
        self.assertTrue(is_surveyor(self.request, xform),
                        'project surveyors are also xform surveyors')
        self.assertTrue(is_surveyor(self.request, media),
                        'project surveyors are also xform surveyors')

        xform.surveyors.clear()
        self.assertEqual(xform.surveyors.count(), 0, 'no custom granted surveyor')

        self.request.user = surveyor
        self.assertFalse(is_surveyor(self.request, xform))
        self.assertFalse(is_surveyor(self.request, media))

        self.request.user = surveyor2
        self.assertTrue(is_surveyor(self.request, xform),
                        'project surveyors are always xform surveyors')
        self.assertTrue(is_surveyor(self.request, media),
                        'project surveyors are always xform surveyors')
