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

import logging
import time

from collections import deque
from concurrent.futures import ProcessPoolExecutor, wait
import multiprocessing as mp

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
        self.pending_submissions = mp.SimpleQueue()
        # save the submissions and entities by their realm
        # this is required to push them back to kernel
        self.processed_submissions = dict()
        self.extracted_entities = dict()

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

        self.pending_submissions.put(task)
        logger.debug(f'Added to queue {task.id}')

        if not self.is_extracting:
            self.is_extracting = True
            mp.Process(target=self.extraction, name='extraction').start()

        if not self.is_pushing_to_kernel:
            self.is_pushing_to_kernel = True
            mp.Process(target=self.push_to_kernel, name='push-to-kernel').start()

    def extraction(self):
        logger.debug('Extracting entities')
        with ProcessPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            processes = []
            while not self.pending_submissions.empty():
                processes.append(
                    executor.submit(self.entity_extraction, self.pending_submissions.get())
                )
            wait(processes)

        if self.is_extracting and not self.pending_submissions.empty():
            self.extraction()
        else:
            self.is_extracting = False
        logger.debug('Entity extraction process finished!')

    def push_to_kernel(self):
        logger.debug('Pushing to kernel')
        with ProcessPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            processes = []

            entity_realms = list(self.extracted_entities.keys())
            for realm in entity_realms:
                processes.append(
                    executor.submit(self.push_entities_to_kernel, realm)
                )

            submission_realms = list(self.processed_submissions.keys())
            for realm in submission_realms:
                processes.append(
                    executor.submit(self.push_submissions_to_kernel, realm)
                )

            wait(processes)

        if self.is_pushing_to_kernel and (self.extracted_entities or self.processed_submissions):
            # wait and check again later
            time.sleep(settings.PUSH_TO_KERNEL_INTERVAL)
            self.push_to_kernel()
        else:
            # continue pushing if entities extraction is in progress
            self.is_pushing_to_kernel = self.is_extracting
        logger.debug('Push to kernel process finished!')

    def entity_extraction(self, task):
        # get artifacts from redis
        # if not found on redis, get from kernel and cache on redis
        # if not found on kernel ==> flag submission as invalid and skip extraction

        tenant = task.tenant
        submission = task.data
        payload = submission[SUBMISSION_PAYLOAD_FIELD]
        submission_entities = []

        # extract entities for each linked mapping
        for mapping_id in submission[ARTEFACT_NAMES.mappings]:
            mapping = get_from_redis_or_kernel(
                id=mapping_id,
                model_type=ARTEFACT_NAMES.mappings,
                tenant=tenant,
                redis=self.redis,
            )

            try:
                # get required artefacts
                schemas = {}
                schema_decorators = mapping['definition']['entities']
                for shemadecorator_id in mapping[ARTEFACT_NAMES.schemadecorators]:
                    sd = get_from_redis_or_kernel(
                        id=shemadecorator_id,
                        model_type=ARTEFACT_NAMES.schemadecorators,
                        tenant=tenant,
                        redis=self.redis,
                    )

                    schema_definition = None
                    if sd and ARTEFACT_NAMES.schema_definition in sd:
                        schema_definition = sd[ARTEFACT_NAMES.schema_definition]

                    elif sd and ARTEFACT_NAMES.schema_id in sd:
                        schema = get_from_redis_or_kernel(
                            id=sd[ARTEFACT_NAMES.schema_id],
                            model_type=ARTEFACT_NAMES.schemas,
                            tenant=settings.DEFAULT_REALM,
                            redis=self.redis,
                        )
                        if schema and schema.get('definition'):
                            schema_definition = schema['definition']

                    if schema_definition:
                        schemas[sd['name']] = schema_definition

                # perform entity extraction
                _, extracted_entities = extract_create_entities(
                    submission_payload=payload,
                    mapping_definition=mapping['definition'],
                    schemas=schemas,
                )

                for entity in extracted_entities:
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

        # add to processed submission queue (but only the required fields)
        self._add_to_tenant_queue(
            tenant,
            self.processed_submissions,
            {
                'id': task.id,
                SUBMISSION_PAYLOAD_FIELD: payload,
                SUBMISSION_EXTRACTION_FLAG: is_extracted,
            }
        )

    def push_entities_to_kernel(self, realm):
        logger.debug(f'Pushing extracted entities for tenant {realm}')

        extracted_entities = self.extracted_entities.pop(realm)
        while len(extracted_entities):
            current_entity_size = get_bulk_size(len(extracted_entities))
            entities = [
                extracted_entities.pop()
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

    def push_submissions_to_kernel(self, realm):
        logger.debug(f'Pushing processed submissions for tenant {realm}')

        processed_submissions = self.processed_submissions.pop(realm)
        while len(processed_submissions):
            current_submission_size = get_bulk_size(len(processed_submissions))
            submissions = [
                processed_submissions.pop()
                for _ in range(current_submission_size)
            ]
            # post submissions to kernel
            try:
                kernel_data_request(
                    url='submissions/bulk_update_extracted.json',
                    method='patch',
                    data=submissions,
                    realm=realm,
                )
                # remove submissions from redis
                for submission in submissions:
                    remove_from_redis(
                        id=submission['id'],
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

    def _add_to_tenant_queue(self, tenant, queue, element):
        try:
            queue[tenant].appendleft(element)
        except KeyError:
            queue[tenant] = deque([element])
