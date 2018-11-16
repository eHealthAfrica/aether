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

from django_rq import get_scheduler

MESSAGE_ERROR = _('RQ scheduler has no running workers.') + '\n'
MESSAGE_OK = _('RQ scheduler running with {number} workers.') + '\n'


class Command(BaseCommand):

    help = _('Health check for RQ.')

    def handle(self, *args, **options):
        '''
        Health check for RQ.
        '''

        scheduler = get_scheduler('default')
        jobs = scheduler.get_jobs()

        if len(jobs) == 0:
            self.stderr.write(MESSAGE_ERROR)
            raise RuntimeError(MESSAGE_ERROR)

        self.stdout.write(MESSAGE_OK.format(number=len(jobs)))
