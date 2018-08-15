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

from datetime import datetime
from django.apps import AppConfig
from django_rq import get_scheduler


class Config(AppConfig):
    name = 'aether.sync'
    verbose_name = 'Aether CouchDB-Sync'

    def ready(self):
        # schedule jobs
        scheduler = get_scheduler('default')

        # Delete any existing job to prevent duplicating them
        for job in scheduler.get_jobs():
            job.delete()

        # run the sync import task every hour since now
        scheduler.schedule(
            scheduled_time=datetime.utcnow(),
            func='aether.sync.tasks.import_synced_devices_task',
            interval=15 * 60,
        )
