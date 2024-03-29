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

from django.contrib.auth import get_user_model
from django.db import models


class DigestCounter(models.Model):

    server_nonce = models.TextField()
    client_nonce = models.TextField()
    client_counter = models.IntegerField(null=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'collect'
        constraints = [
            models.UniqueConstraint(fields=['server_nonce', 'client_nonce'], name='unique_digest_counter'),
        ]


class DigestPartial(models.Model):

    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    username = models.TextField()
    digest = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'collect'
        constraints = [
            models.UniqueConstraint(fields=['user', 'username'], name='unique_digest_partial'),
        ]
