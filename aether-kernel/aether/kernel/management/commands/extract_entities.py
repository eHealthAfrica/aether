#!/usr/bin/env python

# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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
from django.utils.translation import gettext as _

from aether.python.entity.extractor import ENTITY_EXTRACTION_ERRORS as KEY

from aether.kernel.api.models import Submission, Entity
from aether.kernel.api.entity_extractor import run_extraction


class Command(BaseCommand):

    help = _(
        'Extract entities from submissions one by one. '
        'WARNING: The chosen MERGE strategy is the OVERWRITE one.'
    )

    def handle(self, *args, **options):
        '''
        Extract entities from submissions one by one.
        '''

        def print_errors(id, errors):
            self.stderr.write('----------------------------------------')
            self.stderr.write(_('Error on submission {id}.').format(id=id))
            for error in errors:
                self.stderr.write(str(error))
            self.stderr.write('----------------------------------------')

        submissions = Submission.objects.all()
        self.stdout.write(
            _('Number of submissions to handle: {count}').format(count=submissions.count())
        )

        for submission in submissions:
            run_extraction(submission, overwrite=True)
            if submission.payload.get(KEY):
                print_errors(id=submission.pk, errors=submission.payload[KEY])

        self.stdout.write(
            _('Number of entities created: {count}').format(
                count=Entity.objects.exclude(submission__isnull=True).count()
            )
        )
        self.stdout.write(_('END.'))
