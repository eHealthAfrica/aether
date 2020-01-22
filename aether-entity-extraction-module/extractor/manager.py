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

import collections
import logging
import time

from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    extract_create_entities,
)

from extractor import settings
from extractor.utils import (
    ARTEFACT_NAMES,
    SUBMISSION_EXTRACTION_FLAG,
    SUBMISSION_PAYLOAD_FIELD,

    cache_failed_entities,
    get_bulk_size,
    get_from_redis_or_kernel,
    get_redis_keys_by_pattern,
    get_redis_subscribed_message,
    kernel_data_request,
    remove_from_redis,
    redis_subscribe,
)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class ExtractionManager():

    def __init__(self, redis=None):
        self.pending_submissions = collections.deque()
        # save the submissions and entities by their realm
        # this is required to push them back to kernel
        self.processed_submissions = {}
        self.extracted_entities = {}

        self.redis = redis

        self.is_extracting = False
        self.is_pushing_to_kernel = False

    def stop(self):
        self.is_extracting = False
        self.is_pushing_to_kernel = False

    def subscribe_to_redis_channel(self, callback: callable, channel: str):
        redis_subscribe(callback=callback, pattern=channel, redis=self.redis)

    def handle_pending_submissions(self, channel='*'):
        for key in get_redis_keys_by_pattern(channel, self.redis):
            self.add_to_queue(get_redis_subscribed_message(key=key, redis=self.redis))

    def add_to_queue(self, task):
        if not task:
            return

        self.pending_submissions.appendleft(task)
        if not self.is_extracting:
            self.is_extracting = True
            Thread(target=self.process, name='extraction-thread').start()

        if not self.is_pushing_to_kernel:
            self.is_pushing_to_kernel = True
            Thread(target=self.push_to_kernel, name='push-to-kernel-thread').start()

    def entity_extraction(self, task):
        # get artifacts from redis
        # if not found on redis, get from kernel and cache on redis
        # if not found on kernel ==> flag submission as invalid and skip extraction

        tenant = task.tenant
        submission = task.data
        payload = submission[SUBMISSION_PAYLOAD_FIELD]

        submission_entities = []

        mapping_ids = submission[ARTEFACT_NAMES.mappings]
        for mapping_id in mapping_ids:
            schemas = {}
            schema_decorators = {}
            mapping = get_from_redis_or_kernel(
                id=mapping_id,
                model_type=ARTEFACT_NAMES.mappings,
                tenant=tenant,
                redis=self.redis,
            )

            if mapping and ARTEFACT_NAMES.schemadecorators in mapping:
                schemadecorator_ids = mapping[ARTEFACT_NAMES.schemadecorators]
                schema_decorators = mapping['definition']['entities']
                for shemadecorator_id in schemadecorator_ids:
                    sd = get_from_redis_or_kernel(
                        id=shemadecorator_id,
                        model_type=ARTEFACT_NAMES.schemadecorators,
                        tenant=tenant,
                        redis=self.redis,
                    )

                    schema_definition = None
                    if sd and ARTEFACT_NAMES.schema_definition in sd:
                        schema_definition = sd[ARTEFACT_NAMES.schema_definition]

                    elif sd and ARTEFACT_NAMES.single_schema in sd:
                        schema = get_from_redis_or_kernel(
                            id=sd[ARTEFACT_NAMES.single_schema],
                            model_type=ARTEFACT_NAMES.schemas,
                            tenant=settings.DEFAULT_REALM,
                            redis=self.redis,
                        )
                        if schema and schema.get('definition'):
                            schema_definition = schema['definition']

                    if schema_definition:
                        schemas[sd['name']] = schema_definition

            # perform entity extraction
            try:
                submission_data, entities = extract_create_entities(
                    submission_payload=payload,
                    mapping_definition=mapping['definition'],
                    schemas=schemas,
                )

                for entity in entities:
                    submission_entities.append({
                        'payload': entity.payload,
                        'status': entity.status,
                        'schemadecorator': schema_decorators[entity.schemadecorator_name],
                        'submission': task.id,
                        'mapping': mapping_id,
                        'mapping_revision': mapping['revision'],
                    })

            except Exception as e:
                try:
                    payload[ENTITY_EXTRACTION_ERRORS].append(str(e))
                except KeyError:
                    payload[ENTITY_EXTRACTION_ERRORS] = [str(e)]

        is_extracted = False
        if not payload.get(ENTITY_EXTRACTION_ERRORS):
            payload.pop(ENTITY_EXTRACTION_ERRORS, None)
            is_extracted = True
            for entity in submission_entities:
                self._add_to_tenant_queue(tenant, self.extracted_entities, entity)

        # add to processed submission queue (only the required fields)
        self._add_to_tenant_queue(
            tenant,
            self.processed_submissions,
            {
                'id': task.id,
                SUBMISSION_PAYLOAD_FIELD: payload,
                SUBMISSION_EXTRACTION_FLAG: is_extracted,
            }
        )

    def process(self):
        with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            while self.pending_submissions:
                executor.submit(self.entity_extraction, self.pending_submissions.pop())

        if self.pending_submissions:
            self.process()
        else:
            self.is_extracting = False

    def push_entities_to_kernel(self):
        logger.debug('Pushing extracted entities')
        for realm in self.extracted_entities:
            current_entity_size = get_bulk_size(len(self.extracted_entities[realm]))
            while current_entity_size:
                entities = [
                    self.extracted_entities[realm].pop()
                    for _ in range(current_entity_size)
                ]
                # post entities to kernel per realm
                try:
                    kernel_data_request(
                        url='entities.json',
                        method='post',
                        data=entities,
                        realm=realm,
                    )
                except Exception as e:
                    logger.error(str(e))
                    # cache failed entities on redis for retries later
                    cache_failed_entities(entities, realm)

                # wait and check again later
                time.sleep(settings.PUSH_TO_KERNEL_INTERVAL)
                # next bunch of entitites
                current_entity_size = get_bulk_size(len(self.extracted_entities[realm]))

        logger.debug('Pushed all entities to kernel')

    def push_submissions_to_kernel(self):
        logger.debug('Pushing processed submissions')
        for realm in self.processed_submissions:
            current_submission_size = get_bulk_size(len(self.processed_submissions[realm]))
            while current_submission_size:
                submissions = [
                    self.processed_submissions[realm].pop()
                    for _ in range(current_submission_size)
                ]
                # post submissions to kernel
                try:
                    submission_ids = kernel_data_request(
                        url='submissions/bulk_update_extracted.json',
                        method='patch',
                        data=submissions,
                        realm=realm,
                    )
                    # remove submissions from redis
                    for submission_id in submission_ids:
                        remove_from_redis(
                            id=submission_id,
                            model_type=ARTEFACT_NAMES.submissions,
                            tenant=realm,
                            redis=self.redis,
                        )
                except Exception as e:
                    logger.error(str(e))
                    # back to the queue ???
                    # self.processed_submissions[realm].extendleft(submissions)

                # wait and check again later
                time.sleep(settings.PUSH_TO_KERNEL_INTERVAL)
                # next bunch of submissions
                current_submission_size = get_bulk_size(len(self.processed_submissions[realm]))

        logger.debug('Pushed all submissions to kernel')

    def push_to_kernel(self):
        logger.debug('Pushing to kernel')
        if self.is_pushing_to_kernel:
            with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
                executor.submit(self.push_entities_to_kernel)
                executor.submit(self.push_submissions_to_kernel)

    def _add_to_tenant_queue(self, tenant, queue, element):
        try:
            queue[tenant].appendleft(element)
        except KeyError:
            queue[tenant] = collections.deque([element])
