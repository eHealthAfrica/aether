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

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS as KEY,
    extract_create_entities,
)
from . import models


@transaction.atomic
def run_entity_extraction(submission, overwrite=False):
    if overwrite:
        # FIXME:
        # there should be a better way to detect the generated entities and
        # replace their payloads with the new ones
        submission.entities.all().delete()
        payload = submission.payload
        payload.pop(KEY, None)
        submission.payload = payload
        submission.is_extracted = False
        submission.save(update_fields=['payload', 'is_extracted'])

    # Extract entity for each mapping in the submission.mappingset
    mappings = submission.mappingset \
                         .mappings \
                         .filter(is_active=True) \
                         .exclude(definition={}) \
                         .exclude(definition__entities__isnull=True) \
                         .exclude(definition__entities={})

    payload = dict(submission.payload)
    for mapping in mappings:
        # Get the primary key of the schemadecorator
        entity_sd_ids = mapping.definition.get('entities')
        # Get the schema of the schemadecorator
        schema_decorators = {
            name: models.SchemaDecorator.objects.get(pk=_id)
            for name, _id in entity_sd_ids.items()
        }
        schemas = {
            name: sd.schema.definition
            for name, sd in schema_decorators.items()
        }
        payload, entities = extract_create_entities(
            submission_payload=payload,
            mapping_definition=mapping.definition,
            schemas=schemas,
            mapping_id=mapping.id,
        )
        for entity in entities:
            models.Entity(
                id=entity.id,
                payload=entity.payload,
                status=entity.status,
                schemadecorator=schema_decorators[entity.schemadecorator_name],
                submission=submission,
                mapping=mapping,
                mapping_revision=mapping.revision,
                project=submission.project,
            ).save()

    # this should include in the submission payload the following properties
    # generated during the extraction:
    # - ``aether_errors``, with all the errors that made not possible
    #   to create the entities.
    # - ``aether_extractor_enrichment``, with the generated values that allow us
    #   to re-execute this process again with the same result.
    submission.payload = payload
    submission.is_extracted = submission.entities.count() > 0
    submission.save(update_fields=['payload', 'is_extracted'])
