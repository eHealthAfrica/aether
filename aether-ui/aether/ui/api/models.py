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

from .utils import validate_pipeline


class Pipeline(ExportModelOperationsMixin('ui_pipeline'), TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    # this is the avro schema
    schema = JSONField(null=True, blank=True, default=dict)

    # this is an example of the data using the avro schema
    input = JSONField(null=True, blank=True, default=dict)

    # the list of available entity types (avro schemas)
    entity_types = JSONField(null=True, blank=True, default=list)

    # this represents the list of mapping rules
    # {
    #    "mapping": [
    #      {'id': ###, 'source': 'jsonpath-input-1', 'destination: 'jsonpath-entity-type-1'},
    #      {'id': ###, 'source': 'jsonpath-input-2', 'destination: 'jsonpath-entity-type-2'},
    #      ...
    #      {'id': ###, 'source': 'jsonpath-input-n', 'destination: 'jsonpath-entity-type-n'},
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
    #      {"path": 'jsonpath-input-a', "description": 'No match for path'},
    #      {"path": 'jsonpath-entity-type-b', "description": 'No match for path'},
    #      ...
    #      # Summary of the error with the extracted entity
    #      {
    #        "description": 'Extracted record did not conform to registered schema',
    #        "data": {"id": 'uuid:####', ...}
    #      }
    #    ]
    # }
    mapping_errors = JSONField(null=True, blank=True, editable=False)
    output = JSONField(null=True, blank=True, editable=False)
    kernel_refs = JSONField(null=True, blank=True, editable=False)
    published_on = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        errors, output = validate_pipeline(self)
        self.mapping_errors = errors
        self.output = output

        super(Pipeline, self).save(*args, **kwargs)

    class Meta:
        app_label = 'ui'
        default_related_name = 'pipelines'
        ordering = ('name',)
