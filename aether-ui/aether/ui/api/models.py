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

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext as _
from django_prometheus.models import ExportModelOperationsMixin
from model_utils.models import TimeStampedModel

from aether.common.multitenancy.models import MtModelAbstract, MtModelChildAbstract
from aether.common.utils import json_prettified

from .utils import validate_contract


'''
Data model schema:

+------------------+     +------------------+     +------------------+
| Project          |     | Pipeline         |     | Contract         |
+==================+     +==================+     +==================+
| project_id       |<-+  | id               |<-+  | id               |
| name             |  |  | created          |  |  | created          |
+------------------+  |  | modified         |  |  | modified         |
                      |  | name             |  |  | name             |
                      |  | schema           |  |  | entity_types     |
                      |  | input            |  |  | mapping_rules    |
                      |  +~~~~~~~~~~~~~~~~~~+  |  | mapping_errors   |
                      |  | mappingset       |  |  | output           |
                      |  +::::::::::::::::::+  |  | is_active        |
                      +-<| project          |  |  | is_read_only     |
                         +------------------+  |  +~~~~~~~~~~~~~~~~~~+
                                               |  | mapping          |
                                               |  | kernel_refs      |
                                               |  +::::::::::::::::::+
                                               +-<| pipeline         |
                                                  +------------------+
'''


class Project(ExportModelOperationsMixin('ui_project'), TimeStampedModel, MtModelAbstract):
    '''
    Database link of an Aether Kernel Project.

    :ivar UUID  project_id:  Aether Kernel project ID (primary key).
    :ivar text  name:        Project name (might match the linked Kernel project name).
    '''

    # This is needed to submit data to kernel
    # (there is a one to one relation)
    project_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        verbose_name=_('project ID'),
        help_text=_('This ID corresponds to an Aether Kernel project ID.'),
    )
    name = models.TextField(null=True, blank=True, default='', verbose_name=_('name'))
    is_default = models.BooleanField(
        default=False,
        editable=False,
        verbose_name=_('is the default project?'),
    )

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'ui'
        default_related_name = 'projects'
        ordering = ['name']
        verbose_name = _('project')
        verbose_name_plural = _('projects')


class Pipeline(ExportModelOperationsMixin('ui_pipeline'), TimeStampedModel, MtModelChildAbstract):
    '''
    Pipeline

    :ivar UUID      id:          ID (primary key).
    :ivar datetime  created:     Creation timestamp.
    :ivar datetime  modified:    Last update timestamp.
    :ivar text      name:        Name.
    :ivar JSON      schema:      AVRO schema of the input.
    :ivar JSON      input:       Data sample.
    :ivar UUID      mappingset:  Linked Aether Mappingset ID.
    :ivar Project   project:     Project.
    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    name = models.TextField(verbose_name=_('name'))

    # this is the avro schema
    schema = JSONField(null=True, blank=True, default=dict, verbose_name=_('AVRO schema'))

    # this is an example of the data using the avro schema
    input = JSONField(null=True, blank=True, default=dict, verbose_name=_('input JSON'))

    # this is a reference to the linked kernel mappingset
    mappingset = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        verbose_name=_('mapping set ID'),
        help_text=_('This ID corresponds to an Aether Kernel mapping set ID.'),
    )

    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, verbose_name=_('project'))

    @property
    def schema_prettified(self):
        return json_prettified(self.schema)

    @property
    def input_prettified(self):
        return json_prettified(self.input)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Pipeline, self).save(*args, **kwargs)
        # revalidate linked contracts against updated fields
        contracts = Contract.objects.filter(pipeline=self)
        [contract.save() for contract in contracts]

    def get_mt_instance(self):
        return self.project

    class Meta:
        app_label = 'ui'
        default_related_name = 'pipelines'
        ordering = ('name',)
        verbose_name = _('pipeline')
        verbose_name_plural = _('pipelines')
        indexes = [
            models.Index(fields=['project', '-modified']),
            models.Index(fields=['-modified']),
        ]


class Contract(ExportModelOperationsMixin('ui_contract'), TimeStampedModel, MtModelChildAbstract):
    '''
    Contract

    :ivar UUID      id:              ID (primary key).
    :ivar datetime  created:         Creation timestamp.
    :ivar datetime  modified:        Last update timestamp.
    :ivar text      name:            Name.
    :ivar Pipeline  pipeline:        Pipeline.
    :ivar JSON      entity_types:    List of AVRO schemas of the different entities.
    :ivar JSON      mapping_rules:   List of mapping rules used to transform
        the pipeline input into the entity types.
        Rule format:
            {
                "id": uuid,
                "source": "jsonpath-input-1",
                "destination": "jsonpath-entity-type-1",
            }

    :ivar JSON      mapping_errors:  List of errors derived from
        the mapping rules, the entity types and the pipeline input
        when the Kernel ``validate-mappings`` endpoint is called.

    :ivar JSON      output:          List of entities extracted using
        the mapping rules, the entity types and the pipeline input
        when the Kernel ``validate-mappings`` endpoint is called.

    :ivar UUID      mapping:         Linked Aether Mapping ID.
    :ivar JSON      kernel_refs:     Linked Aether Kernel artefact IDs.
        Object expected format:
            {
                "entities": {
                    "entity name": uuid,  # the Kernel project schema ID
                    ...
                },
                "schemas": {
                    "entity name": uuid,  # the Kernel schema ID
                    ...
                },
            }

    :ivar datetime  published_on:    Timestamp of last published to Aether Kernel.
    :ivar bool      is_active:       Is the contract active?
    :ivar bool      is_read_only:    Can the contract be modified manually?

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, verbose_name=_('ID'))
    name = models.TextField(verbose_name=_('name'))

    pipeline = models.ForeignKey(to=Pipeline, on_delete=models.CASCADE, verbose_name=_('pipeline'))

    # the list of available entity types (avro schemas)
    entity_types = JSONField(null=True, blank=True, default=list, verbose_name=_('entity types'))

    # this represents the list of mapping rules
    # {
    #    "mapping_rules": [
    #      {"id": ###, "source": "jsonpath-input-1", "destination": "jsonpath-entity-type-1"},
    #      {"id": ###, "source": "jsonpath-input-2", "destination": "jsonpath-entity-type-2"},
    #      ...
    #      {"id": ###, "source": "jsonpath-input-n", "destination": "jsonpath-entity-type-n"},
    #    ]
    # }
    mapping_rules = JSONField(null=True, blank=True, default=list, verbose_name=_('mapping rules'))

    # these represent the list of entities and errors returned by the
    # `validate-mapping` endpoint in kernel.
    # {
    #    "entities": [
    #      {...},
    #      {...},
    #    ],
    #    "mapping_errors": [
    #      {"path": "jsonpath-input-a", "description": "No match for path"},
    #      {"path": "jsonpath-entity-type-b", "description": "No match for path"},
    #      ...
    #      # Summary of the error with the extracted entity
    #      {
    #        "description": "Extracted record did not conform to registered schema",
    #        "data": {"id": "uuid:####", ...}
    #      }
    #    ]
    # }
    mapping_errors = JSONField(null=True, blank=True, editable=False, verbose_name=_('mapping errors'))
    output = JSONField(null=True, blank=True, editable=False, verbose_name=_('output'))

    # this is a reference to the linked kernel mapping
    mapping = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        verbose_name=_('mapping ID'),
        help_text=_('This ID corresponds to an Aether Kernel mapping ID.'),
    )

    # this contains the information related to the linked artefacts in kernel
    # {
    #     "entities": {
    #         "entity name": uuid,  # the Kernel project schema ID
    #         ...
    #     },
    #     "schemas": {
    #         "entity name": uuid,  # the Kernel schema ID
    #         ...
    #     },
    # }
    kernel_refs = JSONField(
        null=True,
        blank=True,
        editable=False,
        verbose_name=_('Kernel artefact IDs'),
        help_text=_('These IDs correspond to Aether Kernel artefact IDs.'),
    )

    published_on = models.DateTimeField(null=True, blank=True, editable=False, verbose_name=_('published on'))
    is_active = models.BooleanField(default=True, verbose_name=_('is active?'))

    # the read only property is fulfilled by kernel fetched mappings
    is_read_only = models.BooleanField(default=False, editable=False, verbose_name=_('is read only?'))

    @property
    def entity_types_prettified(self):
        return json_prettified(self.entity_types)

    @property
    def mapping_rules_prettified(self):
        return json_prettified(self.mapping_rules)

    @property
    def mapping_errors_prettified(self):
        return json_prettified(self.mapping_errors)

    @property
    def output_errors_prettified(self):
        return json_prettified(self.output)

    @property
    def kernel_refs_errors_prettified(self):
        return json_prettified(self.kernel_refs)

    @property
    def kernel_rules(self):
        '''
        The contract mapping_rules property corresponds
        to definition mapping but with different rules format
        '''
        return [
            [rule['source'], rule['destination']]
            for rule in (self.mapping_rules or [])
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        errors, output = validate_contract(self)
        self.mapping_errors = errors
        self.output = output

        super(Contract, self).save(*args, **kwargs)

    def get_mt_instance(self):
        return self.pipeline.project

    class Meta:
        app_label = 'ui'
        default_related_name = 'contracts'
        ordering = ('name',)
        verbose_name = _('contract')
        verbose_name_plural = _('contracts')
        indexes = [
            models.Index(fields=['pipeline', '-modified']),
            models.Index(fields=['-modified']),
        ]
