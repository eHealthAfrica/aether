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

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from aether.sync.api.couchdb_file import load_file


class Command(BaseCommand):

    help = _('POST file content into CouchDB server.')

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            '-f',
            type=str,
            help=_('Indicate the file to load'),
            dest='filename',
            action='store',
            required=False,
        )

    def handle(self, *args, **options):
        with open(options['filename'], 'r') as fp:
            stats = load_file(fp)
            self.stdout.write(str(stats))

        self.stdout.write(_('END.'))
