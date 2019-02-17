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

from aether.sync.couchdb.setup import create_db, SYSTEM_DATABASES


class Command(BaseCommand):
    '''
    Since CouchDB 2.x the three system databases are not created by default.
    We need to create them manually.

    http://docs.couchdb.org/en/stable/setup/single-node.html

        curl -X PUT http://127.0.0.1:5984/_users
        curl -X PUT http://127.0.0.1:5984/_replicator
        curl -X PUT http://127.0.0.1:5984/_global_changes

    '''

    help = _('Set up CouchDB server.')

    def handle(self, *args, **options):
        for db_name in SYSTEM_DATABASES:
            create_db(db_name)

        self.stdout.write(_('CouchDB set up done.'))
