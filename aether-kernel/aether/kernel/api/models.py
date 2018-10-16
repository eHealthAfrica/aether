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
from django.utils.translation import ugettext as _
from django_prometheus.models import ExportModelOperationsMixin

from model_utils.models import TimeStampedModel

from aether.common.utils import resolve_file_url

from .constants import NAMESPACE
from .utils import json_prettified

STATUS_CHOICES = (
    ('Pending Approval', _('Pending Approval')),
    ('Publishable', _('Publishable')),
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
    | family           |   |  |   | is_encrypted     |   | |   | is_read_only     |  +---<| mapping          |
    +------------------+   |  |   +::::::::::::::::::+   | |   +::::::::::::::::::+       | mapping_rev      |
                           |  +--<| project          |   | +--<| mappingset       |   +--<| projectschema    |
                           +-----<| schema           |   +---<<| projectschemas   |   |   | project(**)      |
                                  +------------------+   |     | project(**)      |   |   +------------------+
                                                         |     +------------------+   |
                                                         +----------------------------+
'''


class Project(ExportModelOperationsMixin('kernel_project'), TimeStampedModel):
    '''
    Project

    :ivar UUID id:        ID.
    :ivar text revision:  Revision.
    :ivar text name:      Name.

    :ivar text salad_schema:    Salad schema (optional).
        Semantic Annotations for Linked Avro Data (SALAD)
        https://www.commonwl.org/draft-3/SchemaSalad.html
    :ivar text jsonld_context:  JSON LS context (optional).
        JSON for Linking Data
        https://json-ld.org/
    :ivar text rdf_definition:  RDF definition (optional).
        Resource Description Framework
        https://www.w3.org/TR/rdf-schema/

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    salad_schema = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('salad schema'),
        help_text=_(
            'Semantic Annotations for Linked Avro Data (SALAD)  '
            'https://www.commonwl.org/draft-3/SchemaSalad.html'
        ),
    )
    jsonld_context = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('JSON LD context'),
        help_text=_(
            'JSON for Linking Data  '
            'https://json-ld.org/'
        ),
    )
    rdf_definition = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('RDF definition'),
        help_text=_(
            'Resource Description Framework  '
            'https://www.w3.org/TR/rdf-schema/'
        ),
    )

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'projects'
        ordering = ['-modified']
        indexes = [
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('project')
        verbose_name_plural = _('projects')


class MappingSet(ExportModelOperationsMixin('kernel_mappingset'), TimeStampedModel):
    '''
    Mapping Set: collection of mapping rules.

    :ivar UUID id:        ID.
    :ivar text revision:  Revision.
    :ivar text name:      Name.

    :ivar JSON schema:      AVRO schema definition.
    :ivar JSON input:       Sample of data that conform the AVRO schema.
    :ivar Project project:  Project.

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    schema = JSONField(null=True, blank=True, verbose_name=_('AVRO schema'))
    input = JSONField(null=True, blank=True, verbose_name=_('input sample'))

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))

    @property
    def input_prettified(self):
        return json_prettified(self.input)

    @property
    def schema_prettified(self):
        return json_prettified(self.schema)

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
        verbose_name = _('mapping set')
        verbose_name_plural = _('mapping sets')


class Submission(ExportModelOperationsMixin('kernel_submission'), TimeStampedModel):
    '''
    Data submission

    :ivar UUID id:        ID.
    :ivar text revision:  Revision.

    :ivar JSON payload:   Submission content.

    :ivar MappingSet mappingset:  Mapping set.
    :ivar Project    project:     Project (redundant but speed up queries).

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))

    payload = JSONField(verbose_name=_('payload'))

    mappingset = models.ForeignKey(
        to=MappingSet,
        on_delete=models.CASCADE,
        verbose_name=_('mapping set'),
    )

    # redundant but speed up queries
    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('project'),
    )

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    @property
    def name(self):
        return f'{self.mappingset.project.name}-{self.mappingset.name}'

    def save(self, **kwargs):
        self.project = self.mappingset.project
        super(Submission, self).save(**kwargs)

    class Meta:
        app_label = 'kernel'
        default_related_name = 'submissions'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('submission')
        verbose_name_plural = _('submissions')


def __attachment_path__(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<submission_id>/{submission_revision}/filename
    return '{submission}/{revision}/{attachment}'.format(
        submission=instance.submission.id,
        revision=instance.submission_revision,
        attachment=filename,
    )


class Attachment(ExportModelOperationsMixin('kernel_attachment'), TimeStampedModel):
    '''
    Attachment linked to submission.

    :ivar UUID id:    ID.
    :ivar text name:  File name.

    :ivar File       attachment_file:      Path to file.
    :ivar text       md5sum:               File content MD5.

    :ivar Submission submission:           Submission.
    :ivar text       submission_revision:  Submission revision when the attachment was saved.

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))

    # http://www.linfo.org/file_name.html
    # Modern Unix-like systems support long file names, usually up to 255 bytes in length.
    name = models.CharField(max_length=255, verbose_name=_('filename'))

    attachment_file = models.FileField(upload_to=__attachment_path__, verbose_name=_('file'))
    # save attachment hash to check later if the file is not corrupted
    md5sum = models.CharField(blank=True, max_length=36, verbose_name=_('file MD5'))

    submission = models.ForeignKey(to=Submission, on_delete=models.CASCADE, verbose_name=_('submission'))
    submission_revision = models.TextField(verbose_name=_('submission revision'))

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
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')


class Schema(ExportModelOperationsMixin('kernel_schema'), TimeStampedModel):
    '''
    AVRO Schema

    :ivar UUID id:        ID.
    :ivar text revision:  Revision.
    :ivar text name:      Name.

    :ivar text type:       Schema namespace
    :ivar JSON difinition: AVRO schema definiton.
    :ivar text family:     Schema family.

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    type = models.CharField(max_length=50, default=NAMESPACE, verbose_name=_('schema type'))
    definition = JSONField(verbose_name=_('AVRO schema'))

    # this field is used to group different schemas created automatically
    # from different sources but that share a common structure
    family = models.TextField(null=True, blank=True, verbose_name=_('schema family'))

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    @property
    def family_name(self):
        return self.family or self.definition.get('name', self.name)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'kernel'
        default_related_name = 'schemas'
        ordering = ['-modified']
        indexes = [
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('schema')
        verbose_name_plural = _('schemas')


class ProjectSchema(ExportModelOperationsMixin('kernel_projectschema'), TimeStampedModel):
    '''
    Project Schema

    :ivar UUID id:   ID.
    :ivar text name: Name.

    :ivar text  mandatory_fields: The list of mandatory fields included in the AVRO
        schema definition.
    :ivar text  transport_rule:   The transport rule.
    :ivar text  masked_fields:    The list of fields that must be masked before transport.
    :ivar bool  is_encrypted:     Is the transport encrypted?

    :ivar Schema  schema:   Schema.
    :ivar Project project:  Project.

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    mandatory_fields = models.TextField(null=True, blank=True, verbose_name=_('mandatory fields'))
    transport_rule = models.TextField(null=True, blank=True, verbose_name=_('transport rule'))
    masked_fields = models.TextField(null=True, blank=True, verbose_name=_('masked fields'))
    is_encrypted = models.BooleanField(default=False, verbose_name=_('encrypted?'))

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))
    schema = models.ForeignKey(to=Schema, on_delete=models.CASCADE, verbose_name=_('schema'))

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
        verbose_name = _('project schema')
        verbose_name_plural = _('project schemas')


class Mapping(ExportModelOperationsMixin('kernel_mapping'), TimeStampedModel):
    '''
    Mapping rules used to extract quality data from raw submissions.

    :ivar UUID id:        ID.
    :ivar text revision:  Revision.
    :ivar text name:      Name.

    :ivar JSON  definition:    The list of mapping rules between
        a source (submission) and a destination (entity).
    :ivar bool  is_active:     Is the mapping active?
    :ivar bool  is_read_only:  Can the mapping rules be modified manually?

    :ivar MappingSet     mappingset:      Mapping set.
    :ivar ProjectSchema  projectschemas:  The list of project schemas included
        in the mapping rules.
    :ivar Project        project:         Project (redundant but speed up queries).

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    definition = JSONField(verbose_name=_('mapping rules'))
    is_active = models.BooleanField(default=True, verbose_name=_('active?'))
    is_read_only = models.BooleanField(default=False, verbose_name=_('read only?'))

    mappingset = models.ForeignKey(
        to=MappingSet,
        on_delete=models.CASCADE,
        verbose_name=_('mapping set'),
    )
    projectschemas = models.ManyToManyField(
        to=ProjectSchema,
        blank=True,
        editable=False,
        verbose_name=_('project schemas'),
    )

    # redundant but speed up queries
    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('project'),
    )

    def save(self, *args, **kwargs):
        self.project = self.mappingset.project
        self.projectschemas.clear()
        super(Mapping, self).save(*args, **kwargs)
        entities = self.definition.get('entities', {})
        ps_list = []
        for entity_pk in entities.values():
            ps_list.append(ProjectSchema.objects.get(pk=entity_pk, project=self.project))
        self.projectschemas.add(*ps_list)

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
        verbose_name = _('mapping')
        verbose_name_plural = _('mappings')


class Entity(ExportModelOperationsMixin('kernel_entity'), models.Model):
    '''
    Entity: extracted data from raw submissions.

    :ivar UUID id:        ID.
    :ivar text revision:  Revision.

    :ivar JSON  payload:   The extracted data.
    :ivar text  status:    Status: "Pending Approval" or "Publishable".
    :ivar text  modified:  Last modified timestamp with ID or previous modified timestamp.

    :ivar Submission     submission:        Submission.
    :ivar Mapping        mapping:           Mapping rules applied to get the entity.
    :ivar text           mapping_revision:  Mapping revision at the moment of the extraction.
    :ivar ProjectSchema  projectschema:     The AVRO schema of the extracted data.
    :ivar Project        project:           Project (redundant but speed up queries).

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))

    payload = JSONField(verbose_name=_('payload'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name=_('status'))
    modified = models.CharField(max_length=100, editable=False, verbose_name=_('modified'))

    submission = models.ForeignKey(
        to=Submission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('submission'),
    )
    mapping = models.ForeignKey(
        to=Mapping,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('mapping'),
    )
    mapping_revision = models.TextField(verbose_name=_('mapping revision'))
    projectschema = models.ForeignKey(
        to=ProjectSchema,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('project schema'),
    )

    # redundant but speed up queries
    project = models.ForeignKey(
        to=Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('project'),
    )

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    @property
    def name(self):
        # try to build a name for the extracted entity base on the linked data
        if self.projectschema and self.mapping:
            # find in the mapping definition the name used by this project schema
            for k, v in self.mapping.definition.get('entities', {}).items():
                if v == str(self.projectschema.pk):
                    return f'{self.project.name}-{k}'
        if self.projectschema:
            return f'{self.project.name}-{self.projectschema.schema.family_name}'
        if self.submission:
            return self.submission.name
        if self.project:
            return self.project.name
        return None

    def save(self, **kwargs):
        if self.submission and self.projectschema:
            if self.submission.project != self.projectschema.project:
                raise IntegrityError(_('Submission and Project Schema MUST belong to the same Project'))
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

    class Meta:
        app_label = 'kernel'
        default_related_name = 'entities'
        verbose_name_plural = 'entities'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('entity')
        verbose_name_plural = _('entities')
