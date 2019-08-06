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
from django.db.models import Count
from django.conf import settings
from django.forms.models import model_to_dict
from aether.sdk.redis.task import TaskHelper

from .constants import SUBMISSION_BULK_UPDATEABLE_FIELDS, MergeOptions as MERGE_OPTIONS
from . import models


REDIS_TASK = TaskHelper(settings)


def object_contains(test, obj):
    # Recursive object comparison function.
    if obj == test:
        return True
    if isinstance(obj, list):
        return True in [object_contains(test, i) for i in obj]
    elif isinstance(obj, dict):
        return True in [object_contains(test, i) for i in obj.values()]
    return False


def merge_objects(source, target, direction):
    # Merge 2 objects
    #
    # Default merge operation is prefer_new
    # Params <source='Original object'>, <target='New object'>,
    # <direction='Direction of merge, determins primacy:
    # use constants.MergeOptions.[prefer_new, prefer_existing]'>
    # # direction Options:
    # prefer_new > (Target to Source) Target takes primacy,
    # prefer_existing > (Source to Target) Source takes primacy
    result = {}
    if direction == MERGE_OPTIONS.fww.value:
        for key in source:
            target[key] = source[key]
        result = target
    elif direction == MERGE_OPTIONS.lww.value:
        for key in target:
            source[key] = target[key]
        result = source
    else:
        result = target
    return result


def get_unique_schemas_used(mappings_ids):
    result = {}
    schemas = models.Schema.objects.filter(schemadecorators__mappings__id__in=mappings_ids)
    for schema in schemas:
        other_linked_mappings = models.Mapping.objects.filter(
            schemadecorators__schema__id=schema.id
        ).exclude(id__in=mappings_ids)
        result[schema.name] = {
            'id': schema.id,
            'name': schema.definition['name'],
        }
        result[schema.name]['is_unique'] = not other_linked_mappings
    return result


@transaction.atomic
def bulk_delete_by_mappings(delete_opts={}, mappingset_id=None, mapping_ids=[]):
    '''
    Bulk delete submissions, entities and schemas uniquely
    linked to the supplied mappings or mappingset

    Arguments:

    delete_opts: {
        # dict of artefacts to be deleted

        'entities': True | False,
        'schemas': True | False,
        'submissions': True | False
    },

    # the uuid of the mappingset to delete it's artefacts.
    # No need to provide mappings if mappingset exists.
    mappingset_id: 'uuid',

    mapping_ids:  [
        # a list of mapping uuids to delete related artefacts,

        'uuid-1',
        'uuid-2'
    ]

    returned result: {
        # a dict of deleted artefacts

        'entities': 34 (int)
        # Number of deleted entities

        'submissions': 34 (int)
        # Number of deleted submissions

        'schemas': {

            # schemas used in the context of the supplied mappings
            # with details on delete operations perform on them or not.
            'Schema-1': {
                # id of the schema
                'id': uuid,

                # name of the schema definition (this can be different from the schema.name)
                'name': string,

                # Flag indicating if the schema is uniquely used in the mappings' context.
                # Delete operations will not be performed if False
                'is_unique': True | False,

                # Flag if delete operation was successful on this schema and cascading objects.
                # Objects with {'is_unique':False} will not have this property
                'is_deleted': True | False,

                # Reason for a delete failure, only available if {'is_deleted': False}
                'reason': string
            },
            'Schema-2': {
                ...
            },
            ...
        }

    }
    '''

    if mappingset_id:
        mapping_ids = models.Mapping.objects.filter(mappingset=mappingset_id).values_list('id', flat=True)
    result = {}
    entities_opt = delete_opts.get('entities')
    schemas_opt = delete_opts.get('schemas')
    submissions_opt = delete_opts.get('submissions')
    if entities_opt is True:
        entities = models.Entity.objects.filter(mapping__id__in=mapping_ids)
        by_schemas_list = list(
            models.Schema.objects.filter(schemadecorators__entities__in=entities)
            .annotate(count=Count('schemadecorators__entities'))
            .values('count', 'name')
        )
        entity_count = entities.count()
        entities.delete()
        result['entities'] = {'total': entity_count, 'schemas': by_schemas_list}

    if schemas_opt is True:
        schema_deletables = get_unique_schemas_used(mapping_ids)
        for key, value in schema_deletables.items():
            if value['is_unique'] is True:
                schema_to_be_deleted = models.Schema.objects.get(pk=value['id'])
                try:
                    schema_to_be_deleted.delete()
                    schema_deletables[key]['is_deleted'] = True
                except Exception as e:  # pragma: no cover
                    schema_deletables[key]['is_deleted'] = False
                    schema_deletables[key]['reason'] = str(e)
        result['schemas'] = schema_deletables

    if submissions_opt is True and mappingset_id:
        submissions = models.Submission.objects.filter(mappingset=mappingset_id)
        submission_count = submissions.count()
        submissions.delete()
        result['submissions'] = submission_count

    return result


def send_model_item_to_redis(model_item):
    '''
    Registers a model item on redis

    Note: Redis host parameters must be provided as environment variables

    Arguments:
    model_item: Model item to be registered on redis.
    '''

    obj = model_to_dict(model_item)
    model_name = model_item._meta.default_related_name
    realm = model_item.get_realm() \
        if model_name is not models.Schema._meta.default_related_name \
        and model_item.get_realm() else settings.DEFAULT_REALM

    if model_name is models.Entity._meta.default_related_name:
        if settings.WRITE_ENTITIES_TO_REDIS:
            REDIS_TASK.add(obj, model_name, realm)
    elif model_name is models.Submission._meta.default_related_name:
        if not model_item.is_extracted:
            # used to fast track entity extraction
            linked_mappings = model_item.mappingset.mappings.all() \
                .filter(is_active=True).values_list('id', flat=True)
            obj['mappings'] = list(linked_mappings)

            REDIS_TASK.add(obj, model_name, realm)
            REDIS_TASK.publish(obj, model_name, realm)
    elif model_name is models.Mapping._meta.default_related_name:
        obj['schemadecorators'] = list(model_item.schemadecorators.all().values_list('id', flat=True))
        REDIS_TASK.add(obj, model_name, realm)
    else:
        REDIS_TASK.add(obj, model_name, realm)


def submissions_flag_extracted(submissions):
    updated_submissions = []
    for submission in submissions:
        s = models.Submission.objects.get(pk=submission['id'])
        s.is_extracted = submission['is_extracted']
        s.payload = submission['payload']
        updated_submissions.append(s)

    models.Submission.objects.bulk_update(updated_submissions, SUBMISSION_BULK_UPDATEABLE_FIELDS)
    return [
        s['id'] for s in submissions
    ]
