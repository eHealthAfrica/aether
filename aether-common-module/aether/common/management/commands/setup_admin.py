#!/usr/bin/env python

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
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = 'Setup admin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            '-u',
            type=str,
            help='Set the admin username',
            dest='username',
            action='store',
            required=False,
            default='admin',
        )
        parser.add_argument(
            '--password',
            '-p',
            type=str,
            help='Set the admin password',
            dest='password',
            action='store',
            required=True,
        )
        parser.add_argument(
            '--email',
            '-e',
            type=str,
            help='Set the admin e-mail',
            dest='email',
            action='store',
            required=False,
            default='admin@aether.org',
        )
        parser.add_argument(
            '--token',
            '-t',
            type=str,
            help='Set the admin token',
            dest='token',
            action='store',
            required=False,
        )

    def handle(self, *args, **options):
        '''
        Creates an admin user and sets his auth token
        '''
        username = options['username']
        password = options['password']
        email = options['email']

        token_key = options['token']

        user_model = get_user_model().objects

        # create admin user if needed
        if not user_model.filter(username=username).exists():
            user_model.create_superuser(username, email, password)
            print('Created admin user "{username}"'.format(username=username))

        # update password
        admin = user_model.get(username=username)
        admin.set_password(password)
        admin.save()
        print('Updated admin user "{username}"'.format(username=username))

        # Skips if no given token or the auth token app is not installed
        if token_key and 'rest_framework.authtoken' in settings.INSTALLED_APPS:
            from rest_framework.authtoken.models import Token

            # delete previous token
            Token.objects.filter(user=admin).delete()
            # assign token value
            Token.objects.create(user=admin, key=token_key)
            print('Created token for admin user "{username}"'.format(username=username))
