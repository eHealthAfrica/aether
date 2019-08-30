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

from django.db import transaction
from aether.python.entity.extractor import extract_create_entities
from . import models


@transaction.atomic
def run_entity_extraction(submission, overwrite=False):
    if overwrite:
        # FIXME:
        # there should be a better way to detect the generated entities and
        # replace their payloads with the new ones
        submission.entities.all().delete()

    # Extract entity for each mapping in the submission.mappingset
    mappings = submission.mappingset \
                         .mappings \
                         .filter(is_active=True) \
                         .exclude(definition={}) \
                         .exclude(definition__entities__isnull=True) \
                         .exclude(definition__entities={})

    for mapping in mappings:
        # Get the primary key of the schemadecorator
        entity_sd_ids = mapping.definition.get('entities')
        # Get the schema of the schemadecorator
        schema_decorator = {
            name: models.SchemaDecorator.objects.get(pk=_id)
            for name, _id in entity_sd_ids.items()
        }
        schemas = {
            name: ps.schema.definition
            for name, ps in schema_decorator.items()
        }
        _, entities = extract_create_entities(
            submission_payload=submission.payload,
            mapping_definition=mapping.definition,
            schemas=schemas,
        )
        for entity in entities:
            schemadecorator_name = entity.schemadecorator_name
            schemadecorator = schema_decorator[schemadecorator_name]
            entity_instance = models.Entity(
                payload=entity.payload,
                status=entity.status,
                schemadecorator=schemadecorator,
                submission=submission,
                mapping=mapping,
                mapping_revision=mapping.revision
            )
            entity_instance.save()

    # this should include in the submission payload the following properties
    # generated during the extraction:
    # - ``aether_errors``, with all the errors that made not possible
    #   to create the entities.
    # - ``aether_extractor_enrichment``, with the generated values that allow us
    #   to re-execute this process again with the same result.
    submission.save()
