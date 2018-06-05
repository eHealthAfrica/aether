# encoding: utf-8

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

import uuid
from datetime import datetime
from hashlib import md5
from django.contrib.postgres.fields import JSONField
from django.db import models
from model_utils.models import TimeStampedModel

from .utils import json_prettified

STATUS_CHOICES = (
    ('Pending Approval', 'Pending Approval'),
    ('Publishable', 'Publishable'),
)


'''

Data model schema:


    +------------------+          +------------------+       +------------------+       +---------------------+
    | Project          |          | Mapping          |       | Submission       |       | Attachment          |
    +==================+          +==================+       +==================+       +=====================+
    | id               |<-----+   | id               |<--+   | id               |<--+   | id                  |
    | created          |      |   | created          |   |   | created          |   |   | created             |
    | modified         |      |   | modified         |   |   | modified         |   |   | modified            |
    | revision         |      |   | revision         |   |   | revision         |   |   | name                |
    | name             |      |   | name             |   |   | date             |   |   | attachment_file     |
    | salad_schema     |      |   | definition       |   |   | payload          |   |   | md5sum              |
    | jsonld_context   |      |   +::::::::::::::::::+   |   +::::::::::::::::::+   |   +:::::::::::::::::::::+
    | rdf_definition   |      +--<| project          |   +--<| mapping          |   +--<| submission          |
    +------------------+      |   +------------------+       | map_revision     |   |   | submission_revision |
                              |                              +------------------+   |   +---------------------+
                              |                                                     |
    +------------------+      |   +------------------+       +------------------+   |
    | Schema           |      |   | ProjectSchema    |       | Entity           |   |
    +==================+      |   +==================+       +==================+   |
    | id               |<--+  |   | id               |<--+   | id               |   |
    | created          |   |  |   | created          |   |   | modified         |   |
    | modified         |   |  |   | modified         |   |   | revision         |   |
    | revision         |   |  |   | name             |   |   | payload          |   |
    | name             |   |  |   | mandatory_fields |   |   | status           |   |
    | definition       |   |  |   | transport_rule   |   |   +::::::::::::::::::+   |
    | type             |   |  |   | masked_fields    |   |   | submission       |>--+
    +------------------+   |  |   | is_encrypted     |   +--<| projectschema    |
                           |  |   +::::::::::::::::::+       +------------------+
                           |  +--<| project          |
                           +-----<| schema           |
                                  +------------------+

'''


class Project(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')
    name = models.CharField(max_length=50, null=False, unique=True)

    salad_schema = models.TextField(null=True, blank=True)
    jsonld_context = models.TextField(null=True, blank=True)
    rdf_definition = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'projects'
        ordering = ('-modified',)


class Mapping(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')
    name = models.CharField(max_length=50, null=False, unique=True)

    definition = JSONField(blank=False, null=False)

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'mappings'
        ordering = ('-modified',)


class Submission(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')

    map_revision = models.TextField(default='1')
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    payload = JSONField(blank=False, null=False)

    mapping = models.ForeignKey(to=Mapping, related_name='submissions', on_delete=models.CASCADE)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return '{} - {}'.format(str(self.mapping), self.id)

    class Meta:
        app_label = 'kernel'
        default_related_name = 'submissions'
        ordering = ('-modified',)


def __attachment_path__(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<submission_id>/{submission_revision}/filename
    return '{submission}/{revision}/{attachment}'.format(
        submission=instance.submission.id,
        revision=instance.submission_revision,
        attachment=filename,
    )


class Attachment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # http://www.linfo.org/file_name.html
    # Modern Unix-like systems support long file names, usually up to 255 bytes in length.
    name = models.CharField(max_length=255)

    attachment_file = models.FileField(upload_to=__attachment_path__)
    # save attachment hash to check later if the file is not corrupted
    md5sum = models.CharField(blank=True, max_length=36)

    submission = models.ForeignKey(to=Submission, on_delete=models.CASCADE)
    submission_revision = models.TextField()

    @property
    def attachment_path(self):
        return self.attachment_file.path

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # calculate file hash
        md5hash = md5()
        for chunk in self.attachment_file.chunks():
            md5hash.update(chunk)
        self.md5sum = md5hash.hexdigest()

        # assign current submission revision if missing
        if not self.submission_revision:
            self.submission_revision = self.submission.revision

        # assign name if missing
        if not self.name:
            self.name = self.attachment_file.name

        super(Attachment, self).save(*args, **kwargs)

    class Meta:
        app_label = 'kernel'
        default_related_name = 'attachments'
        ordering = ['submission', 'submission_revision', 'name']


class Schema(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')
    name = models.CharField(max_length=50, null=False, unique=True)

    type = models.CharField(max_length=50)
    definition = JSONField(blank=False, null=False)

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'schemas'
        ordering = ('-modified',)


class ProjectSchema(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=50, null=False, unique=True)

    mandatory_fields = models.TextField(null=True, blank=True)
    transport_rule = models.TextField(null=True, blank=True)
    masked_fields = models.TextField(null=True, blank=True)
    is_encrypted = models.BooleanField(default=False)

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)
    schema = models.ForeignKey(to=Schema, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'projectschemas'
        ordering = ('-modified',)


class Entity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')

    payload = JSONField(blank=False, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    modified = models.CharField(max_length=100, editable=False)

    projectschema = models.ForeignKey(to=ProjectSchema, on_delete=models.SET_NULL, null=True)
    submission = models.ForeignKey(to=Submission, on_delete=models.SET_NULL, blank=True, null=True)

    def save(self, **kwargs):
        if self.modified:
            self.modified = '{}-{}'.format(datetime.now().isoformat(), self.modified[27:None])
        else:
            self.modified = '{}-{}'.format(datetime.now().isoformat(), self.id)
        super(Entity, self).save(**kwargs)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return 'Entity {}'.format(self.id)

    class Meta:
        app_label = 'kernel'
        default_related_name = 'entities'
        verbose_name_plural = 'entities'
        ordering = ('-modified',)
