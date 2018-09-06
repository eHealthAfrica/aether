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
from django.db.utils import IntegrityError
from django_prometheus.models import ExportModelOperationsMixin

from model_utils.models import TimeStampedModel

from aether.common.utils import resolve_file_url

from .utils import json_prettified

STATUS_CHOICES = (
    ('Pending Approval', 'Pending Approval'),
    ('Publishable', 'Publishable'),
)


'''
Data model schema:

    +------------------+          +------------------+         +------------------+       +------------------+
    | Project          |          | MappingSet       |         | Submission       |       | Attachment       |
    +==================+          +==================+         +==================+       +==================+
    | id               |<-----+   | id               |<----+   | id               |<---+  | id               |
    | created          |      |   | created          |     |   | created          |    |  | created          |
    | modified         |      |   | modified         |     |   | modified         |    |  | modified         |
    | revision         |      |   | revision         |     |   | revision         |    |  | name             |
    | name             |      |   | name             |     |   | payload          |    |  | attachment_file  |
    | salad_schema     |      |   | input            |     |   +::::::::::::::::::+    |  | md5sum           |
    | jsonld_context   |      |   +::::::::::::::::::+     +--<| mappingset       |    |  +::::::::::::::::::+
    | rdf_definition   |      +--<| project          |     |   | project(**)      |    +-<| submission       |
    +------------------+      |   +------------------+     |   +------------------+    |  | submission_rev   |
                              |                            |                           |  +------------------+
                              |                            |                           |
                              |                            |                           |
                              |                            |                           |
    +------------------+      |   +------------------+     |   +------------------+    |  +------------------+
    | Schema           |      |   | ProjectSchema    |     |   | Mapping          |    |  | Entity           |
    +==================+      |   +==================+     |   +==================+    |  +==================+
    | id               |<--+  |   | id               |<--+ |   | id               |<-+ |  | id               |
    | created          |   |  |   | created          |   | |   | created          |  | |  | modified         |
    | modified         |   |  |   | modified         |   | |   | modified         |  | |  | revision         |
    | revision         |   |  |   | name             |   | |   | revision         |  | |  | payload          |
    | name             |   |  |   | mandatory_fields |   | |   | name             |  | |  | status           |
    | definition       |   |  |   | transport_rule   |   | |   | definition       |  | |  +::::::::::::::::::+
    | type             |   |  |   | masked_fields    |   | |   | is_active        |  | +-<| submission       |
    +------------------+   |  |   | is_encrypted     |   | |   | is_read_only     |  +---<| mapping          |
                           |  |   +::::::::::::::::::+   | |   +::::::::::::::::::+       | mapping_rev      |
                           |  +--<| project          |   | +--<| mappingset       |   +--<| projectschema    |
                           +-----<| schema           |   +---<<| projectschemas   |   |   | project(**)      |
                                  +------------------+   |     | project(**)      |   |   +------------------+
                                                         |     +------------------+   |
                                                         +----------------------------+
'''


class Project(ExportModelOperationsMixin('kernel_project'), TimeStampedModel):

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
        ordering = ['-modified']
        indexes = [
            models.Index(fields=['-modified']),
        ]


class MappingSet(ExportModelOperationsMixin('kernel_mappingset'), TimeStampedModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')
    name = models.CharField(max_length=50, null=False, unique=True)

    input = JSONField(null=True, blank=True)

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)

    @property
    def input_prettified(self):
        return json_prettified(self.input)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'mappingsets'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]


class Submission(ExportModelOperationsMixin('kernel_submission'), TimeStampedModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')

    payload = JSONField(blank=False, null=False)

    mappingset = models.ForeignKey(to=MappingSet, on_delete=models.CASCADE)

    # redundant but speed up queries
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, blank=True, null=True)

    def save(self, **kwargs):
        self.project = self.mappingset.project
        super(Submission, self).save(**kwargs)

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    def __str__(self):
        return '{} - {}'.format(str(self.mappingset), self.id)

    class Meta:
        app_label = 'kernel'
        default_related_name = 'submissions'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]


def __attachment_path__(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<submission_id>/{submission_revision}/filename
    return '{submission}/{revision}/{attachment}'.format(
        submission=instance.submission.id,
        revision=instance.submission_revision,
        attachment=filename,
    )


class Attachment(ExportModelOperationsMixin('kernel_attachment'), TimeStampedModel):

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
    def attachment_file_url(self):
        return resolve_file_url(self.attachment_file.url)

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
        ordering = ['submission__id', 'name']
        indexes = [
            models.Index(fields=['submission', 'name']),
        ]


class Schema(ExportModelOperationsMixin('kernel_schema'), TimeStampedModel):

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
        ordering = ['-modified']
        indexes = [
            models.Index(fields=['-modified']),
        ]


class ProjectSchema(ExportModelOperationsMixin('kernel_projectschema'), TimeStampedModel):

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
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]


class Mapping(ExportModelOperationsMixin('kernel_mapping'), TimeStampedModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')
    name = models.CharField(max_length=50, null=False, unique=True)

    definition = JSONField(blank=False, null=False)
    is_active = models.BooleanField(default=True)
    is_read_only = models.BooleanField(default=False)

    mappingset = models.ForeignKey(to=MappingSet, on_delete=models.CASCADE)
    projectschemas = models.ManyToManyField(to=ProjectSchema)

    # redundant but speed up queries
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, blank=True, null=True)

    def save(self, **kwargs):
        self.project = self.mappingset.project
        entities = self.definition.get('entities', {})
        self.projectschemas.clear()
        for entity_pk in entities.values():
            self.projectschemas.add(ProjectSchema.objects.get(pk=entity_pk, project=self.project))

        super(Mapping, self).save(**kwargs)

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'mappings'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]


class Entity(ExportModelOperationsMixin('kernel_entity'), models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')

    payload = JSONField(blank=False, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    modified = models.CharField(max_length=100, editable=False)

    projectschema = models.ForeignKey(to=ProjectSchema, on_delete=models.SET_NULL, null=True)
    submission = models.ForeignKey(to=Submission, on_delete=models.SET_NULL, blank=True, null=True)
    mapping = models.ForeignKey(to=Mapping, on_delete=models.SET_NULL, null=True)
    mapping_revision = models.TextField(blank=False, null=False)

    # redundant but speed up queries
    project = models.ForeignKey(to=Project, on_delete=models.SET_NULL, blank=True, null=True)

    def save(self, **kwargs):
        if self.submission and self.projectschema:
            if self.submission.project != self.projectschema.project:
                raise IntegrityError('Submission and Project Schema MUST belong to the same Project')
            self.project = self.submission.project
        elif self.submission:
            self.project = self.submission.project
        elif self.projectschema:
            self.project = self.projectschema.project

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
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
