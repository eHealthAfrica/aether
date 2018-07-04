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
    | name             |      |   | name             |   |   | payload          |   |   | attachment_file     |
    | salad_schema     |      |   | definition       |   |   +::::::::::::::::::+   |   | md5sum              |
    | jsonld_context   |      |   +::::::::::::::::::+   +--<| mapping          |   |   +:::::::::::::::::::::+
    | rdf_definition   |      +--<| project          |       | map_revision     |   +--<| submission          |
    +------------------+      |   +------------------+       +------------------+   |   | submission_revision |
                              |                                                     |   +---------------------+
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
    '''
                Table "public.kernel_project"

         Column     |           Type           | Modifiers
    ----------------+--------------------------+-----------
     id             | uuid                     | not null
     revision       | text                     | not null
     name           | character varying(50)    | not null
     salad_schema   | text                     |
     jsonld_context | text                     |
     rdf_definition | text                     |
     created        | timestamp with time zone | not null
     modified       | timestamp with time zone | not null

    Indexes:
        "kernel_project_pkey" PRIMARY KEY, btree (id)
        "kernel_project_name_###_uniq" UNIQUE CONSTRAINT, btree (name)
        "kernel_project_name_###_like" btree (name varchar_pattern_ops)

    Referenced by:
        TABLE "kernel_mapping"
            CONSTRAINT "kernel_mapping_project_id_###_fk_kernel_project_id"
            FOREIGN KEY (project_id)
            REFERENCES kernel_project(id)
            DEFERRABLE INITIALLY DEFERRED

        TABLE "kernel_projectschema"
            CONSTRAINT "kernel_projectschema_project_id_###_fk_kernel_project_id"
            FOREIGN KEY (project_id)
            REFERENCES kernel_project(id)
            DEFERRABLE INITIALLY DEFERRED

    '''

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
    '''
                Table "public.kernel_mapping"

       Column   |           Type           | Modifiers
    ------------+--------------------------+-----------
     id         | uuid                     | not null
     name       | character varying(50)    | not null
     definition | jsonb                    | not null
     revision   | text                     | not null
     project_id | uuid                     | not null
     created    | timestamp with time zone | not null
     modified   | timestamp with time zone | not null

    Indexes:
        "kernel_mapping_pkey" PRIMARY KEY, btree (id)
        "kernel_mapping_name_###_uniq" UNIQUE CONSTRAINT, btree (name)
        "kernel_mapping_name_###_like" btree (name varchar_pattern_ops)
        "kernel_mapping_project_id_###" btree (project_id)

    Foreign-key constraints:
        "kernel_mapping_project_id_###_fk_kernel_project_id"
            FOREIGN KEY (project_id)
            REFERENCES kernel_project(id)
            DEFERRABLE INITIALLY DEFERRED

    Referenced by:
        TABLE "kernel_submission"
            CONSTRAINT "kernel_submission_mapping_id_###_fk_kernel_mapping_id"
            FOREIGN KEY (mapping_id)
            REFERENCES kernel_mapping(id)
            DEFERRABLE INITIALLY DEFERRED

    '''

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
    '''
                Table "public.kernel_submission"

        Column    |           Type           | Modifiers
    --------------+--------------------------+-----------
     id           | uuid                     | not null
     revision     | text                     | not null
     map_revision | text                     | not null
     payload      | jsonb                    | not null
     mapping_id   | uuid                     | not null
     created      | timestamp with time zone | not null
     modified     | timestamp with time zone | not null

    Indexes:
        "kernel_submission_pkey" PRIMARY KEY, btree (id)
        "kernel_submission_mapping_id_###" btree (mapping_id)

    Foreign-key constraints:
        "kernel_submission_mapping_id_###_fk_kernel_mapping_id"
            FOREIGN KEY (mapping_id)
            REFERENCES kernel_mapping(id)
            DEFERRABLE INITIALLY DEFERRED

    Referenced by:
        TABLE "kernel_attachment"
            CONSTRAINT "kernel_attachment_submission_id_###_fk_kernel_submission_id"
            FOREIGN KEY (submission_id)
            REFERENCES kernel_submission(id)
            DEFERRABLE INITIALLY DEFERRED

        TABLE "kernel_entity"
            CONSTRAINT "kernel_entity_submission_id_###_fk_kernel_submission_id"
            FOREIGN KEY (submission_id)
            REFERENCES kernel_submission(id)
            DEFERRABLE INITIALLY DEFERRED

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')

    map_revision = models.TextField(default='1')
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
    '''
                Table "public.kernel_attachment"

           Column        |           Type           | Modifiers
    ---------------------+--------------------------+-----------
     id                  | uuid                     | not null
     submission_revision | text                     | not null
     name                | character varying(255)   | not null
     attachment_file     | character varying(100)   | not null
     md5sum              | character varying(36)    | not null
     submission_id       | uuid                     | not null
     created             | timestamp with time zone | not null
     modified            | timestamp with time zone | not null

    Indexes:
        "kernel_attachment_pkey" PRIMARY KEY, btree (id)
        "kernel_attachment_submission_id_###" btree (submission_id)

    Foreign-key constraints:
        "kernel_attachment_submission_id_###_fk_kernel_submission_id"
            FOREIGN KEY (submission_id)
            REFERENCES kernel_submission(id)
            DEFERRABLE INITIALLY DEFERRED

    '''

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
    '''
                Table "public.kernel_schema"

       Column   |           Type           | Modifiers
    ------------+--------------------------+-----------
     id         | uuid                     | not null
     name       | character varying(50)    | not null
     type       | character varying(50)    | not null
     definition | jsonb                    | not null
     revision   | text                     | not null
     created    | timestamp with time zone | not null
     modified   | timestamp with time zone | not null

    Indexes:
        "kernel_schema_pkey" PRIMARY KEY, btree (id)
        "kernel_schema_name_###_uniq" UNIQUE CONSTRAINT, btree (name)
        "kernel_schema_name_###_like" btree (name varchar_pattern_ops)

    Referenced by:
        TABLE "kernel_projectschema"
            CONSTRAINT "kernel_projectschema_schema_id_###_fk_kernel_schema_id"
            FOREIGN KEY (schema_id)
            REFERENCES kernel_schema(id)
            DEFERRABLE INITIALLY DEFERRED
    '''

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
    '''
                Table "public.kernel_projectschema"

          Column      |           Type           | Modifiers
    ------------------+--------------------------+-----------
     id               | uuid                     | not null
     name             | character varying(50)    | not null
     mandatory_fields | text                     |
     transport_rule   | text                     |
     masked_fields    | text                     |
     is_encrypted     | boolean                  | not null
     project_id       | uuid                     | not null
     schema_id        | uuid                     | not null
     created          | timestamp with time zone | not null
     modified         | timestamp with time zone | not null

    Indexes:
        "kernel_projectschema_pkey" PRIMARY KEY, btree (id)
        "kernel_projectschema_name_###_uniq" UNIQUE CONSTRAINT, btree (name)
        "kernel_projectschema_name_###_like" btree (name varchar_pattern_ops)
        "kernel_projectschema_project_id_###" btree (project_id)
        "kernel_projectschema_schema_id_###" btree (schema_id)

    Foreign-key constraints:
        "kernel_projectschema_project_id_###_fk_kernel_project_id"
            FOREIGN KEY (project_id)
            REFERENCES kernel_project(id)
            DEFERRABLE INITIALLY DEFERRED

        "kernel_projectschema_schema_id_###_fk_kernel_schema_id"
            FOREIGN KEY (schema_id)
            REFERENCES kernel_schema(id)
            DEFERRABLE INITIALLY DEFERRED

    Referenced by:
        TABLE "kernel_entity"
            CONSTRAINT "kernel_entity_projectschema_id_###_fk_kernel_project_id"
            FOREIGN KEY (projectschema_id)
            REFERENCES kernel_projectschema(id)
            DEFERRABLE INITIALLY DEFERRED

    '''

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


class Entity(TimeStampedModel):
    '''
                Table "public.kernel_entity"

          Column      |          Type          | Modifiers
    ------------------+------------------------+-----------
     id               | uuid                   | not null
     revision         | text                   | not null
     payload          | jsonb                  | not null
     status           | character varying(20)  | not null
     modified         | character varying(100) | not null
     projectschema_id | uuid                   |
     submission_id    | uuid                   |

    Indexes:
        "kernel_entity_pkey" PRIMARY KEY, btree (id)
        "kernel_entity_projectschema_id_###" btree (projectschema_id)
        "kernel_entity_submission_id_###" btree (submission_id)

    Foreign-key constraints:
        "kernel_entity_projectschema_id_###_fk_kernel_project_id"
            FOREIGN KEY (projectschema_id)
            REFERENCES kernel_projectschema(id)
            DEFERRABLE INITIALLY DEFERRED

        "kernel_entity_submission_id_###_fk_kernel_submission_id"
            FOREIGN KEY (submission_id)
            REFERENCES kernel_submission(id)
            DEFERRABLE INITIALLY DEFERRED

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.TextField(default='1')

    payload = JSONField(blank=False, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    projectschema = models.ForeignKey(to=ProjectSchema, on_delete=models.SET_NULL, null=True)
    submission = models.ForeignKey(to=Submission, on_delete=models.SET_NULL, blank=True, null=True)

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
