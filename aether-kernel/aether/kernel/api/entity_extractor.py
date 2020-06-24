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
from rest_framework.decorators import action
from rest_framework.response import Response

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS as KEY,
    extract_create_entities,
)

from .models import SchemaDecorator, Submission, Entity
from .utils import send_model_item_to_redis


class ExtractMixin(object):

    @action(detail=True, methods=['patch'])
    def extract(self, request, pk, *args, **kwargs):
        '''
        Executes the entity extraction for the submission or the linked submissions.

        Optionally expects as query parameter:

        - `overwrite` to indicate that even the submissions with extracted
          entities should repeat the extraction process. It's only taken into
          consideration for projects or mapping sets, single submissions are
          always processed.

        Reachable at ``PATCH /{model}/{pk}/extract/``
        '''

        instance = self.get_object_or_404(pk=pk)

        if isinstance(instance, Submission):
            run_extraction(instance, True, True)

        else:
            overwrite = bool(self.request.query_params.get('overwrite'))
            if overwrite:
                submissions = instance.submissions.all()
            else:
                submissions = instance.submissions.filter(is_extracted=False)

            # send to EXM if the number of submissions is too big
            local = submissions.count() < 100

            for submission in submissions:
                run_extraction(submission, overwrite, local)

        return Response(
            data=self.serializer_class(instance, context={'request': request}).data,
        )


def run_extraction(submission, overwrite=False, local=True):
    if local:
        try:
            run_entity_extraction(submission, overwrite)
        except Exception as e:
            # capture here the exception so the transaction can rollback any
            # changed ocurred during the extraction
            submission.payload[KEY] = submission.payload.get(KEY, [])
            submission.payload[KEY] += [str(e)]
            submission.save(update_fields=['payload'])
    else:
        send_model_item_to_redis(submission)


@transaction.atomic
def run_entity_extraction(submission, overwrite=False):
    if overwrite:
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

    for mapping in mappings:
        # Get the primary key of the schemadecorator
        entity_sd_ids = mapping.definition.get('entities')
        # Get the schema of the schemadecorator
        schema_decorator = {
            name: SchemaDecorator.objects.get(pk=_id)
            for name, _id in entity_sd_ids.items()
        }
        schemas = {
            name: sd.schema.definition
            for name, sd in schema_decorator.items()
        }
        _, entities = extract_create_entities(
            submission_payload=submission.payload,
            mapping_definition=mapping.definition,
            schemas=schemas,
        )

        for entity in entities:
            Entity(
                payload=entity.payload,
                status=entity.status,
                schemadecorator=schema_decorator[entity.schemadecorator_name],
                submission=submission,
                mapping=mapping,
                mapping_revision=mapping.revision,
                project=submission.project,
            ).save()

    submission.is_extracted = submission.entities.count() > 0
    submission.save(update_fields=['payload', 'is_extracted'])
