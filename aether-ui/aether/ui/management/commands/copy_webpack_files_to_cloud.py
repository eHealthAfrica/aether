#!/usr/bin/env python

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

import os
import json
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _
from django.core.files.storage import default_storage
from django.core.files import File


class Command(BaseCommand):

    help = _(
        'Uploads webpack static files to the default django storage'
    )

    def handle(self, *args, **options):
        webpack_dir = '/code/aether/ui/assets/bundles'
        CDN_URL = os.environ.get('CDN_URL', '/ui-assets/static')
        for file_name in os.listdir(webpack_dir):
            file_path = os.path.join(webpack_dir, file_name)
            if os.path.isfile(file_path):
                file = File(open(file_path, 'rb'))
                if file_name == 'webpack-stats.json':
                    stats = json.loads(file.read())
                    for key in stats['chunks']:
                        for item in stats['chunks'][key]:
                            name = item['name']
                            item['pubicPath'] = f'{CDN_URL}/{name}'
                    file = File(open(file_path, 'w'))
                    file.write(json.dumps(stats))
                    file = File(open(file_path, 'rb'))
                default_storage.save(file_name, file)
                file.close()
