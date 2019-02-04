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
from django_prometheus.models import ExportModelOperationsMixin
from model_utils.models import TimeStampedModel

from .utils import validate_contract


'''
Data model schema:

+------------------+     +------------------+
| Pipeline         |     | Contract         |
+==================+     +==================+
| id               |<-+  | id               |
| created          |  |  | created          |
| modified         |  |  | modified         |
| name             |  |  | name             |
| schema           |  |  | entity_types     |
| input            |  |  | mapping          |
+~~~~~~~~~~~~~~~~~~+  |  | mapping_errors   |
| mappingset       |  |  | output           |
+------------------+  |  | is_active        |
                      |  | is_read_only     |
                      |  +~~~~~~~~~~~~~~~~~~+
                      |  | kernel_refs      |
                      |  +::::::::::::::::::+
                      +-<| pipeline         |
                         +------------------+
'''


class Pipeline(ExportModelOperationsMixin('ui_pipeline'), TimeStampedModel):
    '''
    Pipeline

    :ivar UUID      id:          ID (primary key).
    :ivar datetime  created:     Creation timestamp.
    :ivar datetime  modified:    Last update timestamp.
    :ivar text      name:        Name (**unique**).
    :ivar JSON      schema:      AVRO schema of the input.
    :ivar JSON      input:       Data sample.
    :ivar UUID      mappingset:  Linked Aether Mappingset ID.
    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    # this is the avro schema
    schema = JSONField(null=True, blank=True, default=dict)

    # this is an example of the data using the avro schema
    input = JSONField(null=True, blank=True, default=dict)

    # this is a reference to the linked kernel mappingset
    mappingset = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Pipeline, self).save(*args, **kwargs)
        # revalidate linked contracts against updated fields
        contracts = Contract.objects.filter(pipeline=self)
        [contract.save() for contract in contracts]

    class Meta:
        app_label = 'ui'
        default_related_name = 'pipelines'
        ordering = ('name',)


class Contract(ExportModelOperationsMixin('ui_contract'), TimeStampedModel):
    '''
    Contract

    :ivar UUID      id:              ID (primary key).
    :ivar datetime  created:         Creation timestamp.
    :ivar datetime  modified:        Last update timestamp.
    :ivar text      name:            Name (**unique**).
    :ivar Pipeline  pipeline:        Pipeline.
    :ivar JSON      entity_types:    List of AVRO schemas of the different entities.
    :ivar JSON      mapping:         List of mapping rules used to transform
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

    :ivar JSON      kernel_refs:     Linked Aether Kernel artefact IDs.
        Object expected format:
            {
                "project": uuid,
                "mapping": uuid,
                "schemas": {
                    "entity name": uuid,
                    ...
                },
            }

    :ivar datetime  published_on:    Timestamp of last published to Aether Kernel.
    :ivar bool      is_active:       Is the contract active?
    :ivar bool      is_read_only:    Can the contract be modified manually?

    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    pipeline = models.ForeignKey(to=Pipeline, on_delete=models.CASCADE)

    # the list of available entity types (avro schemas)
    entity_types = JSONField(null=True, blank=True, default=list)

    # this represents the list of mapping rules
    # {
    #    "mapping": [
    #      {"id": ###, "source": "jsonpath-input-1", "destination": "jsonpath-entity-type-1"},
    #      {"id": ###, "source": "jsonpath-input-2", "destination": "jsonpath-entity-type-2"},
    #      ...
    #      {"id": ###, "source": "jsonpath-input-n", "destination": "jsonpath-entity-type-n"},
    #    ]
    # }
    mapping = JSONField(null=True, blank=True, default=list)

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
    mapping_errors = JSONField(null=True, blank=True, editable=False)
    output = JSONField(null=True, blank=True, editable=False)

    # this contains the information related to the linked artefacts in kernel
    # {
    #     "project": uuid,
    #     "mapping": uuid,
    #     "schemas": {
    #         "entity name": uuid,
    #         ...
    #     },
    # }
    kernel_refs = JSONField(null=True, blank=True, editable=False)

    published_on = models.DateTimeField(null=True, blank=True, editable=False)
    is_active = models.BooleanField(default=True)
    is_read_only = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        errors, output = validate_contract(self)
        self.mapping_errors = errors
        self.output = output

        super(Contract, self).save(*args, **kwargs)

    class Meta:
        app_label = 'ui'
        default_related_name = 'contracts'
        ordering = ['pipeline__id', '-modified']
        indexes = [
            models.Index(fields=['pipeline', '-modified']),
            models.Index(fields=['-modified']),
        ]
