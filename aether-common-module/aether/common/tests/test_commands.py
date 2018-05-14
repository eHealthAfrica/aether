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

import os

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.core.management import call_command
from django.test import TestCase

from rest_framework.authtoken.models import Token


UserModel = get_user_model().objects


class TestSetupAdminCommand(TestCase):

    def setUp(self):
        # Redirect to /dev/null in order to not clutter the test log.
        self.out = open(os.devnull, 'w')

    def test__password_argument_is_required(self):
        self.assertRaises(
            CommandError,
            call_command,
            'setup_admin',
            stdout=self.out,
        )

        self.assertRaises(
            CommandError,
            call_command,
            'setup_admin',
            '--username=admin',
            stdout=self.out,
        )

    def test__creates_new_admin_user(self):
        self.assertFalse(UserModel.filter(username='admin_test').exists())
        call_command('setup_admin', '--username=admin_test', '-p=adminadmin', stdout=self.out)
        self.assertTrue(UserModel.filter(username='admin_test').exists())

    def test__updates_existing_user(self):
        user = UserModel.create_user(username='admin', password='adminadmin')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        call_command('setup_admin', '-p=secretsecret', stdout=self.out)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test__creates_token(self):
        self.assertFalse(UserModel.filter(username='admin').exists())
        self.assertEqual(Token.objects.all().count(), 0)
        call_command('setup_admin', '-p=adminadmin', '-t=12345', stdout=self.out)
        self.assertTrue(UserModel.filter(username='admin').exists())
        self.assertEqual(Token.objects.all().count(), 1)
