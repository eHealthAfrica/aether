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

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..aether_tags import get_fullname, prettified


class AetherTagsTests(TestCase):

    def test_get_fullname(self):
        user = get_user_model().objects.create()

        self.assertEqual(get_fullname(user), '')
        self.assertEqual(get_fullname(user), str(user))
        self.assertEqual(get_fullname(user), user.username)

        user.username = 'user-name'
        self.assertEqual(get_fullname(user), str(user))
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = 'first'
        user.last_name = ''
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = ''
        user.last_name = 'last'
        self.assertEqual(get_fullname(user), user.username)

        user.first_name = 'first'
        user.last_name = 'last'
        self.assertEqual(get_fullname(user), 'first last')

    def test_prettified(self):
        data = {}
        expected = '<pre><span></span><span class="p">{}</span>\n</pre>'

        pretty = str(prettified(data))
        self.assertIn(expected, pretty)
