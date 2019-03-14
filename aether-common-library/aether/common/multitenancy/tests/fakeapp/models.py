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
from django.db import models

from aether.common.multitenancy.models import MtModelAbstract, MtModelChildAbstract


class TestModel(MtModelAbstract):
    name = models.TextField()

    user = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='+',
        to=settings.AUTH_USER_MODEL,
    )

    class Meta:
        app_label = 'fakeapp'


class TestChildModel(MtModelChildAbstract):
    name = models.TextField()
    parent = models.ForeignKey(to=TestModel, on_delete=models.CASCADE, related_name='children')

    def get_mt_instance(self):
        return self.parent

    class Meta:
        app_label = 'fakeapp'


class TestGrandChildModel(MtModelChildAbstract):
    name = models.TextField()
    parent = models.ForeignKey(to=TestChildModel, on_delete=models.CASCADE, related_name='children')

    # does not implement the missing method
    # def get_mt_instance(self):
    #     return self.parent.parent

    class Meta:
        app_label = 'fakeapp'


class TestNoMtModel(models.Model):
    name = models.TextField()

    class Meta:
        app_label = 'fakeapp'
