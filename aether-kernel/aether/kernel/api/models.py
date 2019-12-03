# encoding: utf-8

# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import transaction, models, IntegrityError
from django.utils.translation import gettext as _
from django_prometheus.models import ExportModelOperationsMixin

from model_utils.models import TimeStampedModel

from aether.sdk.multitenancy.models import MtModelAbstract, MtModelChildAbstract
from aether.sdk.utils import json_prettified, get_file_content

from aether.python.exceptions import ValidationError as AetherValidationError
from aether.python.validators import validate_entity_payload

from .constants import NAMESPACE
from .validators import (
    wrapper_validate_mapping_definition,
    wrapper_validate_schema_definition,
    wrapper_validate_schema_input_definition,
)


ENTITY_STATUS_CHOICES = (
    ('Pending Approval', _('Pending Approval')),
    ('Publishable', _('Publishable')),
)

FILE_PATH_MAX_LENGTH = 500


'''
Data model schema:

+------------------+       +------------------+       +------------------+       +---------------------+
| Project          |       | MappingSet       |       | Submission       |       | Attachment          |
+==================+       +==================+       +==================+       +=====================+
| Base fields      |<---+  | Base fields      |<---+  | Base fields      |<---+  | Base fields         |
| active           |    |  | input            |    |  | payload          |    |  | attachment_file     |
| salad_schema     |    |  | schema           |    |  +::::::::::::::::::+    |  | md5sum              |
| jsonld_context   |    |  +::::::::::::::::::+    +-<| mappingset       |    |  +:::::::::::::::::::::+
| rdf_definition   |    +-<| project          |    |  | project(**)      |    +-<| submission          |
+::::::::::::::::::+    |  +------------------+    |  +------------------+    |  | submission_revision |
| organizations(*) |    |                          |                          |  +---------------------+
+------------------+    |                          |                          |
                        |                          |                          |
+------------------+    |  +------------------+    |  +------------------+    |  +------------------+
| Schema           |    |  | SchemaDecorator  |    |  | Mapping          |    |  | Entity           |
+==================+    |  +==================+    |  +==================+    |  +==================+
| Base fields      |<-+ |  | Base fields      |<-+ |  | Base fields      |<-+ |  | Base fields      |
| definition       |  | |  | mandatory_fields |  | |  | definition       |  | |  | payload          |
| type             |  | |  | transport_rule   |  | |  | is_active        |  | |  | status           |
| family           |  | |  | masked_fields    |  | |  | is_read_only     |  | |  +::::::::::::::::::+
+------------------+  | |  | is_encrypted     |  | |  +::::::::::::::::::+  | +-<| submission       |
                      | |  +::::::::::::::::::+  | +-<| mappingset       |  +---<| mapping          |
                      | +-<| project          |  +==<<| schemadecorators |  |    | mapping_revision |
                      +---<| schema           |  |    | project(**)      |  +---<| schemadecorator  |
                           +------------------+  |    +------------------+  |    | project(**)      |
                                                 +--------------------------+    | schema(**)       |
                                                                                 +------------------+
'''


class KernelAbstract(TimeStampedModel):
    '''
    Common fields in all models:

    :ivar UUID  id:        ID (primary key).
    :ivar text  revision:  Revision.
    :ivar text  name:      Name (**unique**).

    .. note:: Extends from :class:`model_utils.models.TimeStampedModel`

        :ivar datetime  created:   Creation timestamp.
        :ivar datetime  modified:  Last update timestamp.
    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    revision = models.TextField(default='1', verbose_name=_('revision'))
    name = models.TextField(verbose_name=_('name'))

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        app_label = 'kernel'
        ordering = ['-modified']


class Project(ExportModelOperationsMixin('kernel_project'), KernelAbstract, MtModelAbstract):
    '''
    Project

    .. note:: Extends from :class:`aether.kernel.api.models.KernelAbstract`
    .. note:: Extends from :class:`aether.sdk.multitenancy.models.MultitenancyBaseAbstract`

    :ivar bool      active:          Active. Defaults to ``True``.
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

    active = models.BooleanField(default=True, verbose_name=_('active'))
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

    def delete(self, *args, **kwargs):
        # find the linked passthrough schemas
        for schema in Schema.objects.filter(family=str(self.pk)):
            # delete the schema if is not used in more projects
            if schema.schemadecorators.exclude(project=self).count() == 0:
                schema.delete()
            else:
                schema.family = None  # remove passthrough flag
                schema.save()

        super(Project, self).delete(*args, **kwargs)

    class Meta:
        default_related_name = 'projects'
        ordering = ['-modified']
        indexes = [
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('project')
        verbose_name_plural = _('projects')


class ProjectChildAbstract(KernelAbstract, MtModelChildAbstract):
    '''
    Use this model class for each Project dependant model.

    .. note:: Extends from :class:`aether.kernel.api.models.KernelAbstract`
    '''

    def get_mt_instance(self):
        return self.project

    class Meta:
        abstract = True


class MappingSet(ExportModelOperationsMixin('kernel_mappingset'), ProjectChildAbstract):
    '''
    Mapping Set: collection of mapping rules.

    .. note:: Extends from :class:`aether.kernel.api.models.ProjectChildAbstract`

    :ivar JSON      schema:    AVRO schema definition.
    :ivar JSON      input:     Sample of data that conform the AVRO schema.
    :ivar Project   project:   Project.

    '''

    schema = JSONField(
        null=True,
        blank=True,
        validators=[wrapper_validate_schema_input_definition],
        verbose_name=_('AVRO schema'),
    )
    input = JSONField(null=True, blank=True, verbose_name=_('input sample'))

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))

    @property
    def input_prettified(self):
        return json_prettified(self.input)

    @property
    def schema_prettified(self):
        return json_prettified(self.schema)

    def clean(self, *args, **kwargs):
        super(MappingSet, self).clean(*args, **kwargs)

        if self.schema and self.input:
            try:
                validate_entity_payload(
                    schema_definition=self.schema,
                    payload=self.input,
                )
            except AetherValidationError:
                raise ValidationError({'input': _('Input does not conform to schema')})

    def save(self, *args, **kwargs):
        try:
            # this will call the fields validators in our case
            # `wrapper_validate_schema_input_definition`
            self.full_clean()
        except ValidationError as ve:
            raise IntegrityError(ve)

        super(MappingSet, self).save(*args, **kwargs)

    class Meta:
        default_related_name = 'mappingsets'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('mapping set')
        verbose_name_plural = _('mapping sets')


class Submission(ExportModelOperationsMixin('kernel_submission'), ProjectChildAbstract):
    '''
    Data submission

    .. note:: Extends from :class:`aether.kernel.api.models.ProjectChildAbstract`

    :ivar JSON        payload:     Submission content.
    :ivar MappingSet  mappingset:  Mapping set.
    :ivar Project     project:     Project (redundant but speed up queries).

    '''

    payload = JSONField(verbose_name=_('payload'))

    mappingset = models.ForeignKey(
        to=MappingSet,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('mapping set'),
    )

    # redundant but speed up queries
    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        verbose_name=_('project'),
    )

    @property
    def payload_prettified(self):
        return json_prettified(self.payload)

    @property
    def name(self):  # overrides base model field
        name = self.mappingset.name if self.mappingset else self.id
        return f'{self.project.name}-{name}'

    def save(self, *args, **kwargs):
        self.project = self.mappingset.project if self.mappingset else self.project
        super(Submission, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.id}'

    class Meta:
        default_related_name = 'submissions'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('submission')
        verbose_name_plural = _('submissions')


def __attachment_path__(instance, filename):
    # file will be uploaded to [{tenant}/]__attachments__/{project}/{submission}/{filename}
    realm = instance.get_realm()
    return '{tenant}__attachments__/{project}/{submission}/{attachment}'.format(
        tenant=f'{realm}/' if realm else '',
        project=instance.submission.project.pk,
        submission=instance.submission.pk,
        attachment=filename,
    )


class Attachment(ExportModelOperationsMixin('kernel_attachment'), ProjectChildAbstract):
    '''
    Attachment linked to submission.

    .. note:: Extends from :class:`aether.kernel.api.models.ProjectChildAbstract`

    :ivar File        attachment_file:      Path to file (depends on the file storage system).
    :ivar text        md5sum:               File content hash (MD5).
    :ivar Submission  submission:           Submission.
    :ivar text        submission_revision:  Submission revision when the attachment was saved.

    '''

    name = models.TextField(verbose_name=_('filename'))

    attachment_file = models.FileField(
        max_length=FILE_PATH_MAX_LENGTH,
        upload_to=__attachment_path__,
        verbose_name=_('file'),
    )
    # save attachment hash to check later if the file is not corrupted
    md5sum = models.CharField(blank=True, max_length=36, verbose_name=_('file MD5'))

    submission = models.ForeignKey(to=Submission, on_delete=models.CASCADE, verbose_name=_('submission'))
    submission_revision = models.TextField(verbose_name=_('submission revision'))

    @property
    def revision(self):  # overrides base model field
        return None

    @property
    def project(self):
        return self.submission.project

    def get_content(self, as_attachment=False):
        return get_file_content(self.name, self.attachment_file.url, as_attachment)

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
        default_related_name = 'attachments'
        ordering = ['submission__id', 'name']
        indexes = [
            models.Index(fields=['submission', 'name']),
        ]
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')


class Schema(ExportModelOperationsMixin('kernel_schema'), KernelAbstract):
    '''
    AVRO Schema

    .. note:: Extends from :class:`aether.kernel.api.models.KernelAbstract`

    :ivar text      type:        Schema namespace
    :ivar JSON      definition:  AVRO schema definiton.
    :ivar text      family:      Schema family.

    '''

    name = models.TextField(unique=True, verbose_name=_('name'))
    type = models.TextField(default=NAMESPACE, verbose_name=_('schema type'))
    definition = JSONField(validators=[wrapper_validate_schema_definition], verbose_name=_('AVRO schema'))

    # this field is used to group different schemas created automatically
    # from different sources but that share a common structure
    # the passthrough schemas will contain the project id as family
    family = models.TextField(null=True, blank=True, verbose_name=_('schema family'))

    @property
    def definition_prettified(self):
        return json_prettified(self.definition)

    @property
    def schema_name(self):
        return self.definition.get('name', self.name)

    class Meta:
        default_related_name = 'schemas'
        ordering = ['-modified']
        indexes = [
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('schema')
        verbose_name_plural = _('schemas')


class SchemaDecorator(ExportModelOperationsMixin('kernel_schemadecorator'), ProjectChildAbstract):
    '''
    Schema Decorator

    .. note:: Extends from :class:`aether.kernel.api.models.ProjectChildAbstract`

    :ivar text      mandatory_fields:  The list of mandatory fields included in
        the AVRO schema definition.
    :ivar text      transport_rule:    The transport rule.
    :ivar text      masked_fields:     The list of fields that must be masked before transport.
    :ivar bool      is_encrypted:      Is the transport encrypted?
    :ivar JSON      topic:             The kafka topic reference
    :ivar Schema    schema:            Schema.
    :ivar Project   project:           Project.

    '''

    mandatory_fields = models.TextField(null=True, blank=True, verbose_name=_('mandatory fields'))
    transport_rule = models.TextField(null=True, blank=True, verbose_name=_('transport rule'))
    masked_fields = models.TextField(null=True, blank=True, verbose_name=_('masked fields'))
    is_encrypted = models.BooleanField(default=False, verbose_name=_('encrypted?'))
    topic = JSONField(null=True, blank=True, verbose_name=_('topic'))

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))
    schema = models.ForeignKey(to=Schema, on_delete=models.CASCADE, verbose_name=_('schema'))

    @property
    def revision(self):  # overrides base model field
        return None

    @property
    def topic_prettified(self):
        return json_prettified(self.topic)

    def save(self, *args, **kwargs):
        if self.topic is None:
            self.topic = {'name': self.name}
        super(SchemaDecorator, self).save(*args, **kwargs)

    class Meta:
        default_related_name = 'schemadecorators'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('schema decorator')
        verbose_name_plural = _('schema decorators')


class Mapping(ExportModelOperationsMixin('kernel_mapping'), ProjectChildAbstract):
    '''
    Mapping rules used to extract quality data from raw submissions.

    .. note:: Extends from :class:`aether.kernel.api.models.ProjectChildAbstract`

    :ivar JSON              definition:        The list of mapping rules between
        a source (submission) and a destination (entity).
    :ivar bool              is_active:         Is the mapping active?
    :ivar bool              is_read_only:      Can the mapping rules be modified manually?
    :ivar MappingSet        mappingset:        Mapping set.
    :ivar SchemaDecorator   schemadecorators:  The list of schema decorators included
        in the mapping rules.
    :ivar Project           project:           Project (redundant but speed up queries).

    '''

    definition = JSONField(
        validators=[wrapper_validate_mapping_definition],
        verbose_name=_('mapping rules'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('active?'))
    is_read_only = models.BooleanField(default=False, verbose_name=_('read only?'))

    mappingset = models.ForeignKey(
        to=MappingSet,
        on_delete=models.CASCADE,
        verbose_name=_('mapping set'),
    )
    schemadecorators = models.ManyToManyField(
        to=SchemaDecorator,
        blank=True,
        editable=False,
        verbose_name=_('schema decorators'),
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
    def definition_prettified(self):
        return json_prettified(self.definition)

    def save(self, *args, **kwargs):
        try:
            # this will call the fields validators in our case
            # `wrapper_validate_mapping_definition`
            self.full_clean()
        except ValidationError as ve:
            raise IntegrityError(ve)

        self.project = self.mappingset.project
        super(Mapping, self).save(*args, **kwargs)

        self.schemadecorators.set([
            SchemaDecorator.objects.get(pk=entity_pk, project=self.project)
            for entity_pk in self.definition.get('entities', {}).values()
        ])

    def get_mt_instance(self):
        # because project can be null we need to override the method
        return self.mappingset.project

    class Meta:
        default_related_name = 'mappings'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('mapping')
        verbose_name_plural = _('mappings')


class Entity(ExportModelOperationsMixin('kernel_entity'), ProjectChildAbstract):
    '''
    Entity: extracted data from raw submissions.

    .. note:: Extends from :class:`aether.kernel.api.models.ProjectChildAbstract`
        Replaces:
        :ivar text           modified:          Last update timestamp in ISO format along with the id.

    :ivar JSON            payload:           The extracted data.
    :ivar text            status:            Status: "Pending Approval" or "Publishable".
    :ivar text            modified:          Last modified timestamp with ID or previous modified timestamp.
    :ivar Submission      submission:        Submission.
    :ivar Mapping         mapping:           Mapping rules applied to get the entity.
    :ivar text            mapping_revision:  Mapping revision at the moment of the extraction.
    :ivar SchemaDecorator schemadecorator:   The AVRO schema of the extracted data.
    :ivar Project         project:           Project (redundant but speed up queries).
    :ivar Schema          schema :           Schema (redundant but speed up queries).

    '''

    modified = models.CharField(max_length=100, editable=False, verbose_name=_('modified'))

    payload = JSONField(verbose_name=_('payload'))
    status = models.CharField(max_length=20, choices=ENTITY_STATUS_CHOICES, verbose_name=_('status'))

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
    mapping_revision = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('mapping revision'),
    )

    # WARNING:  the schema decorator deletion has consequences
    schemadecorator = models.ForeignKey(
        to=SchemaDecorator,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('schema decorator'),
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
    def name(self):  # overrides base model field
        # try to build a name for the extracted entity base on the linked data
        if self.schemadecorator and self.mapping:
            # find in the mapping definition the name used by this schema decorator
            for k, v in self.mapping.definition.get('entities', {}).items():
                if v == str(self.schemadecorator.pk):
                    return f'{self.project.name}-{k}'
        if self.schemadecorator:
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
        if self.schemadecorator:
            project_ids.add(self.schemadecorator.project.pk)
            possible_project = self.schemadecorator.project
        if self.submission:
            project_ids.add(self.submission.project.pk)
            possible_project = self.submission.project
        if self.mapping:
            project_ids.add(self.mapping.project.pk)
            possible_project = self.mapping.project

        if len(project_ids) > 1:
            raise ValidationError(_('Submission, Mapping and Schema Decorator MUST belong to the same Project'))
        elif len(project_ids) == 1:
            self.project = possible_project

        if self.schemadecorator:  # redundant values taken from schema decorator
            self.schema = self.schemadecorator.schema

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
            except AetherValidationError as ve:
                raise ValidationError({'payload': [str(ve)]})

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
        except Exception as ve:
            raise IntegrityError(ve)

        super(Entity, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.id}'

    def is_accessible(self, realm):
        # because project can be null we need to override the method
        return self.project.is_accessible(realm) if self.project else False

    def get_realm(self):
        # because project can be null we need to override the method
        return self.project.get_realm() if self.project else None

    class Meta:
        default_related_name = 'entities'
        verbose_name_plural = 'entities'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('entity')
        verbose_name_plural = _('entities')


def __task_path__(instance, filename):
    # file will be uploaded to [{tenant}/]__export__/{project}/{task}/{filename}
    realm = instance.get_realm()
    return '{tenant}__export__/{project}/{task}/{filename}'.format(
        tenant=f'{realm}/' if realm else '',
        project=instance.project.pk,
        task=instance.pk,
        filename=filename,
    )


class ExportTask(ExportModelOperationsMixin('kernel_exporttask'), ProjectChildAbstract):
    '''
    List of files generated by an export task.

    .. note:: Extends from :class:`aether.kernel.api.models.ProjectChildAbstract`

    :ivar User         created_by:  User that requested the data.
    :ivar JSON         settings:    The settings to get the requested the data.
    :ivar text         status:      Task status: Initial/In progress/Done/Cancelled.
    :ivar Array[File]  files:       List of generated files.
    :ivar Project      project:     Project.

    '''

    created_by = models.ForeignKey(
        blank=True,
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
        to=get_user_model(),
        verbose_name=_('Requested by'),
    )
    settings = JSONField(
        default=dict,
        editable=False,
        verbose_name=_('settings'),
    )
    status = models.CharField(
        default='INIT',
        editable=False,
        max_length=20,
        verbose_name=_('status'),
    )

    files = ArrayField(
        base_field=models.FileField(
            editable=False,
            max_length=FILE_PATH_MAX_LENGTH,
            upload_to=__task_path__,
            verbose_name=_('file'),
        ),
        blank=True,
        default=list,
        editable=False,
        null=True,
        verbose_name=_('generated files'),
    )

    project = models.ForeignKey(
        blank=True,
        editable=False,
        null=True,
        on_delete=models.CASCADE,
        to=Project,
        verbose_name=_('project'),
    )

    @transaction.atomic
    def add_file(self, filename, file_path):
        self.refresh_from_db()
        with open(file_path, 'rb') as fi:
            self.files.append(File(fi, name=__task_path__(self, filename)))
        self.save(update_fields=['files'])

    @transaction.atomic
    def set_status(self, status):
        self.refresh_from_db()
        self.status = status
        self.save(update_fields=['status'])

    class Meta:
        default_related_name = 'tasks'
        ordering = ['project__id', '-modified']
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
