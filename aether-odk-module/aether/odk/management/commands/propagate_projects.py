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

from aether.odk.api.models import Project
from aether.odk.api.kernel_utils import propagate_kernel_project, KernelPropagationError


class Command(BaseCommand):

    help = _('Propagate ODK projects into Kernel.')

    def handle(self, *args, **options):
        '''
        Propagate projects one by one.
        '''

        self.stdout.write(_('Number of projects to propagate: {count}').format(count=Project.objects.count()))

        index = 0
        for project in Project.objects.all():
            index += 1

            try:
                propagate_kernel_project(project)
                self.stdout.write(
                    str(index) + ' - ' +
                    _('Propagated project "{name}".').format(name=project.name)
                )
            except KernelPropagationError as e:
                self.stderr.write(
                    str(index) + ' - ************* ' +
                    _('Error on project "{name}".').format(name=project.name)
                )
                self.stderr.write(str(e))

        self.stdout.write(_('END.'))
