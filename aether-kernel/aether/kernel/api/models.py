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
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.utils.translation import ugettext as _
from django_prometheus.models import ExportModelOperationsMixin

from model_utils.models import TimeStampedModel

from aether.common.utils import resolve_file_url

from .constants import NAMESPACE
from .utils import json_prettified

from .validators import (
    validate_avro_schema,
    validate_entity_payload,
    validate_mapping_definition,
    validate_schema_definition,
)


ENTITY_STATUS_CHOICES = (
    ('Pending Approval', _('Pending Approval')),
    ('Publishable', _('Publishable')),
)


'''
Data model schema:

+------------------+       +------------------+       +------------------+       +---------------------+
| Project          |       | MappingSet       |       | Submission       |       | Attachment          |
+==================+       +==================+       +==================+       +=====================+
| id               |<---+  | id               |<---+  | id               |<---+  | id                  |
| created          |    |  | created          |    |  | created          |    |  | created             |
| modified         |    |  | modified         |    |  | modified         |    |  | modified            |
| revision         |    |  | revision         |    |  | revision         |    |  | name                |
| name             |    |  | name             |    |  | payload          |    |  | attachment_file     |
| salad_schema     |    |  | input            |    |  +::::::::::::::::::+    |  | md5sum              |
| jsonld_context   |    |  +::::::::::::::::::+    +-<| mappingset       |    |  +:::::::::::::::::::::+
| rdf_definition   |    +-<| project          |    |  | project(**)      |    +-<| submission          |
+------------------+    |  +------------------+    |  +------------------+    |  | submission_revision |
                        |                          |                          |  +---------------------+
                        |                          |                          |
                        |                          |                          |
+------------------+    |  +------------------+    |  +------------------+    |  +------------------+
| Schema           |    |  | ProjectSchema    |    |  | Mapping          |    |  | Entity           |
+==================+    |  +==================+    |  +==================+    |  +==================+
| id               |<-+ |  | id               |<-+ |  | id               |<-+ |  | id               |
| created          |  | |  | created          |  | |  | created          |  | |  | modified         |
| modified         |  | |  | modified         |  | |  | modified         |  | |  | revision         |
| revision         |  | |  | name             |  | |  | revision         |  | |  | payload          |
| name             |  | |  | mandatory_fields |  | |  | name             |  | |  | status           |
| definition       |  | |  | transport_rule   |  | |  | definition       |  | |  +::::::::::::::::::+
| type             |  | |  | masked_fields    |  | |  | is_active        |  | +-<| submission       |
| family           |  | |  | is_encrypted     |  | |  | is_read_only     |  +---<| mapping          |
+------------------+  | |  +::::::::::::::::::+  | |  +::::::::::::::::::+       | mapping_revision |
                      | +-<| project          |  | +-<| mappingset       |  +---<| projectschema    |
                      +---<| schema           |  +--<<| projectschemas   |  |    | project(**)      |
                           +------------------+  |    | project(**)      |  |    | schema(**)       |
                                                 |    +------------------+  |    +------------------+
                                                 +--------------------------+
'''


class CachedManager(models.Manager):
    # Model manager that looks first in the cache.
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._queryset_class = CachedQuerySet


class CachedQuerySet(models.query.QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        self.model_name = model.__name__
        super().__init__(model, query, using, hints)

    def get(self, *args, **kwargs):
        print(args, kwargs)
        if 'pk' or 'id' in kwargs:
            _id = kwargs.get('id') or kwargs.get('pk')
            key = f'''{self.model_name}:{kwargs['pk']}'''
            try:
                obj = cache.get(key)
                if not obj:
                    raise ValueError(f'{key} not in cache')
                return obj
            except ValueError:
                obj = super().get(**kwargs)
                cache.set(key, obj)
                return obj
        else:
            return super().get(**kwargs)


class Project(ExportModelOperationsMixin('kernel_project'), TimeStampedModel):
    '''
    Project

    :ivar UUID      id:              ID (primary key).
    :ivar datetime  created:         Creation timestamp.
    :ivar datetime  modified:        Last update timestamp.
    :ivar text      revision:        Revision.
    :ivar text      name:            Name (**unique**).
    :ivar text      salad_schema:    Salad schema (optional).
        Semantic Annotations for Linked Avro Data (SALAD)
        https://www.commonwl.org/draft-3/SchemaSalad.html
    :ivar text      jsonld_context:  JSON LS context (optional).
        JSON for Linking Data
        https://json-ld.org/
    :ivar text      rdf_definition:  RDF definition (optional).
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
    objects = CachedManager()  # Cache get by PK calls

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # find the linked passthrough schemas
        for schema in Schema.objects.filter(family=str(self.pk)):
            # delete the schema if is not used in more projects
            if schema.projectschemas.exclude(project=self).count() == 0:
                schema.delete()
            else:
                schema.family = None  # remove passthrough flag
                schema.save()

        super(Project, self).delete(*args, **kwargs)

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

    :ivar UUID      id:        ID (primary key).
    :ivar datetime  created:   Creation timestamp.
    :ivar datetime  modified:  Last update timestamp.
    :ivar text      revision:  Revision.
    :ivar text      name:      Name (**unique**).
    :ivar JSON      schema:    AVRO schema definition.
    :ivar JSON      input:     Sample of data that conform the AVRO schema.
    :ivar Project   project:   Project.

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    schema = JSONField(
        null=True,
        blank=True,
        validators=[validate_avro_schema],
        verbose_name=_('AVRO schema'),
    )
    input = JSONField(null=True, blank=True, verbose_name=_('input sample'))

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))
    objects = CachedManager()  # Cache get by PK calls

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

    :ivar UUID        id:          ID (primary key).
    :ivar datetime    created:     Creation timestamp.
    :ivar datetime    modified:    Last update timestamp.
    :ivar text        revision:    Revision.
    :ivar JSON        payload:     Submission content.
    :ivar MappingSet  mappingset:  Mapping set.
    :ivar Project     project:     Project (redundant but speed up queries).

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

    def save(self, *args, **kwargs):
        self.project = self.mappingset.project
        super(Submission, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.id}'

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

    :ivar UUID        id:                   ID (primary key).
    :ivar datetime    created:              Creation timestamp.
    :ivar datetime    modified:             Last update timestamp.
    :ivar text        name:                 File name.
    :ivar File        attachment_file:      Path to file (depends on the file storage system).
    :ivar text        md5sum:               File content hash (MD5).
    :ivar Submission  submission:           Submission.
    :ivar text        submission_revision:  Submission revision when the attachment was saved.

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

    :ivar UUID      id:         ID (primary key).
    :ivar datetime  created:     Creation timestamp.
    :ivar datetime  modified:    Last update timestamp.
    :ivar text      revision:    Revision.
    :ivar text      name:        Name (**unique**).
    :ivar text      type:        Schema namespace
    :ivar JSON      definition:  AVRO schema definiton.
    :ivar text      family:      Schema family.

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    type = models.CharField(max_length=50, default=NAMESPACE, verbose_name=_('schema type'))
    definition = JSONField(validators=[validate_schema_definition], verbose_name=_('AVRO schema'))

    # this field is used to group different schemas created automatically
    # from different sources but that share a common structure
    # the passthrough schemas will contain the project id as family
    family = models.TextField(null=True, blank=True, verbose_name=_('schema family'))
    objects = CachedManager()  # Cache get by PK calls

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    @property
    def schema_name(self):
        return self.definition.get('name', self.name)

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

    :ivar UUID      id:                ID (primary key).
    :ivar datetime  created:           Creation timestamp.
    :ivar datetime  modified:          Last update timestamp.
    :ivar text      name:              Name (**unique**).
    :ivar text      mandatory_fields:  The list of mandatory fields included in
        the AVRO schema definition.
    :ivar text      transport_rule:    The transport rule.
    :ivar text      masked_fields:     The list of fields that must be masked before transport.
    :ivar bool      is_encrypted:      Is the transport encrypted?
    :ivar Schema    schema:            Schema.
    :ivar Project   project:           Project.

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    mandatory_fields = models.TextField(null=True, blank=True, verbose_name=_('mandatory fields'))
    transport_rule = models.TextField(null=True, blank=True, verbose_name=_('transport rule'))
    masked_fields = models.TextField(null=True, blank=True, verbose_name=_('masked fields'))
    is_encrypted = models.BooleanField(default=False, verbose_name=_('encrypted?'))

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))
    schema = models.ForeignKey(to=Schema, on_delete=models.CASCADE, verbose_name=_('schema'))
    objects = CachedManager()  # Cache get by PK calls

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

    :ivar UUID           id:              ID (primary key).
    :ivar datetime       created:         Creation timestamp.
    :ivar datetime       modified:        Last update timestamp.
    :ivar text           revision:        Revision.
    :ivar text           name:            Name (**unique**).
    :ivar JSON           definition:      The list of mapping rules between
        a source (submission) and a destination (entity).
    :ivar bool           is_active:       Is the mapping active?
    :ivar bool           is_read_only:    Can the mapping rules be modified manually?
    :ivar MappingSet     mappingset:      Mapping set.
    :ivar ProjectSchema  projectschemas:  The list of project schemas included
        in the mapping rules.
    :ivar Project        project:         Project (redundant but speed up queries).

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))
    name = models.CharField(max_length=50, unique=True, verbose_name=_('name'))

    definition = JSONField(validators=[validate_mapping_definition], verbose_name=_('mapping rules'))
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
    objects = CachedManager()  # Cache get by PK calls

    def save(self, *args, **kwargs):
        self.project = self.mappingset.project

        try:
            # this will call the fields validators in our case `validate_mapping_definition`
            self.full_clean()
        except ValidationError as ve:
            raise IntegrityError(ve)

        super(Mapping, self).save(*args, **kwargs)

        self.projectschemas.clear()
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

    :ivar UUID           id:                ID (primary key).
    :ivar text           modified:          Last update timestamp in ISO format along with the id.
    :ivar text           revision:          Revision.
    :ivar JSON           payload:           The extracted data.
    :ivar text           status:            Status: "Pending Approval" or "Publishable".
    :ivar text           modified:          Last modified timestamp with ID or previous modified timestamp.
    :ivar Submission     submission:        Submission.
    :ivar Mapping        mapping:           Mapping rules applied to get the entity.
    :ivar text           mapping_revision:  Mapping revision at the moment of the extraction.
    :ivar ProjectSchema  projectschema:     The AVRO schema of the extracted data.
    :ivar Project        project:           Project (redundant but speed up queries).
    :ivar Schema         schema :           Schema (redundant but speed up queries).

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))

    payload = JSONField(verbose_name=_('payload'))
    status = models.CharField(max_length=20, choices=ENTITY_STATUS_CHOICES, verbose_name=_('status'))
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
    mapping_revision = models.TextField(null=True, blank=True, verbose_name=_('mapping revision'))
    projectschema = models.ForeignKey(
        to=ProjectSchema,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('project schema'),
    )

    # redundant but speed up queries
    # WARNING:  the project deletion has consequences
    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('project'),
    )

    # redundant but speed up queries
    # WARNING:  the schema deletion has consequences
    schema = models.ForeignKey(
        to=Schema,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('schema'),
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
            return f'{self.project.name}-{self.schema.schema_name}'
        if self.submission:
            return self.submission.name
        if self.project:
            return self.project.name
        return None

    def clean(self):
        super(Entity, self).clean()

        # check linked projects
        project_ids = set()
        possible_project = None
        if self.projectschema:
            project_ids.add(self.projectschema.project.pk)
            possible_project = self.projectschema.project
        if self.submission:
            project_ids.add(self.submission.project.pk)
            possible_project = self.submission.project
        if self.mapping:
            project_ids.add(self.mapping.project.pk)
            possible_project = self.mapping.project

        if len(project_ids) > 1:
            raise ValidationError(_('Submission, Mapping and Project Schema MUST belong to the same Project'))
        elif len(project_ids) == 1:
            self.project = possible_project

        if self.projectschema:  # redundant values taken from project schema
            self.schema = self.projectschema.schema

        if self.mapping and not self.mapping_revision:
            self.mapping_revision = self.mapping.revision

        if self.modified:
            self.modified = '{}-{}'.format(datetime.now().isoformat(), self.modified[27:None])
        else:
            self.modified = '{}-{}'.format(datetime.now().isoformat(), self.id)

        if self.schema:
            try:
                validate_entity_payload(
                    schema_definition=self.schema.definition,
                    payload=self.payload,
                )
            except ValidationError as ve:
                raise ValidationError({'payload': [str(ve)]})

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
        except ValidationError as ve:
            raise IntegrityError(ve)

        super(Entity, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.id}'

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
