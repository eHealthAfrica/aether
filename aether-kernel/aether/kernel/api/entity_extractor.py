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

import re
from datetime import timedelta

from django.db import transaction
from django.utils.timezone import now

from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    renderer_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS as KEY,
    extract_create_entities,
)

from .models import SchemaDecorator, Submission, Entity
from .utils import send_model_item_to_redis

# The maximum number of submissions that are extracted locally
# instead of sending them to redis => exm.
LOCAL_MAXIMUM = 20

DELTA_UNITS = {
    'd': 'days',
    'h': 'hours',
    'm': 'minutes',
    's': 'seconds',
    'w': 'weeks',
}


class ExtractMixin(object):

    @action(detail=True, methods=['patch'])
    def extract(self, request, pk, *args, **kwargs):
        '''
        Executes the entity extraction for the submission or the linked submissions.

        Optionally expects as query parameters:

        - `overwrite` to indicate that even the submissions with extracted
          entities should repeat the extraction process.
          It's only taken into consideration for projects or mapping sets,
          single submissions are always processed immediately.

        - `schedule` to indicate if the extraction process is executed in
          background by the extraction service and not immediately.
          It's only taken into consideration for projects or mapping sets,
          single submissions are always processed immediately.

        - `delta` to filter the submissions whose last modification time was
          not before the indicated delta `1d` (1 day ago), `weeks2` (2 weeks ago).
          It's only taken into consideration for projects or mapping sets.

        Reachable at ``PATCH /{model}/{pk}/extract/``
        '''

        instance = self.get_object_or_404(pk=pk)

        if isinstance(instance, Submission):
            run_extraction(instance, overwrite=True, schedule=False)

        else:
            overwrite = bool(self.request.query_params.get('overwrite'))
            if overwrite:
                submissions = instance.submissions.all()
            else:
                submissions = instance.submissions.filter(is_extracted=False)

            delta = self.request.query_params.get('delta')
            if delta:
                submissions = submissions.filter(modified__lte=parse_delta(delta))

            # send to EXM if the number of submissions is too big
            schedule = bool(self.request.query_params.get('schedule'))
            schedule = schedule or submissions.count() > LOCAL_MAXIMUM

            for submission in submissions:
                run_extraction(submission, overwrite, schedule)

        return Response(
            data=self.serializer_class(instance, context={'request': request}).data,
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
@renderer_classes([JSONRenderer])
def extract_view(request, *args, **kwargs):
    '''
    Submit to redis the submissions that are not yet extracted and
    whose last modification time was before the indicated delta (1 day).

    Reachable at ``GET|POST /admin/~extract?delta=1d&[submit]``
    '''

    delta = request.query_params.get('delta', '1d')
    modified = parse_delta(delta)
    submissions = Submission \
        .objects \
        .filter(modified__gte=modified) \
        .filter(project__active=True) \
        .order_by('-modified')
    pending = submissions.filter(is_extracted=False)

    submitted = False
    if request.method == 'POST' or 'submit' in request.query_params:
        submitted = True
        for submission in pending.iterator():
            send_model_item_to_redis(submission)

    return Response(data={
        'count': pending.count(),
        'total': submissions.count(),
        'delta': delta,
        'modified': modified,
        'submitted': submitted,
        'timestamp': now(),
    })


def run_extraction(submission, overwrite=False, schedule=False):
    if not schedule:
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

    payload = dict(submission.payload)
    for mapping in mappings:
        # Get the primary key of the schemadecorator
        entity_sd_ids = mapping.definition.get('entities')
        # Get the schema of the schemadecorator
        schema_decorators = {
            name: SchemaDecorator.objects.get(pk=_id)
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
            Entity(
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


def parse_delta(interval):
    try:
        value = list(filter(lambda x: x != '', re.split(r'\D', interval, flags=re.I)))[0]
        unit = list(filter(lambda x: x != '', re.split(r'\d', interval, flags=re.I)))[0]
        unit_name = DELTA_UNITS.get(unit, unit)
        return now() - timedelta(**{unit_name: int(value)})
    except Exception:
        return now() - timedelta(days=1)
