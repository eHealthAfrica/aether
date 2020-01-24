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
from concurrent.futures import ThreadPoolExecutor as PoolExecutor, wait
from threading import Thread as Job

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
    get_from_redis_or_kernel,
    get_redis_keys_by_pattern,
    get_redis_subscribed_message,
    kernel_data_request,
    redis_subscribe,
    redis_unsubscribe,
    remove_from_redis,
)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class ExtractionManager():

    def __init__(self, redis=None):
        self.redis = redis
        self.is_running = False

        self.pending_submissions = deque()

        # save the submissions and entities by their realm
        # this is required to push them back to kernel
        self.processed_submissions = {}
        self.extracted_entities = {}

    def start(self):
        # include the tasks that are already in the redis channel
        self.handle_pending_submissions(settings.SUBMISSION_CHANNEL)

        # creates a thread that reads the new tasks from the redis channel
        # and adds them to our `pending_submissions` queue.
        # WARNING: This thread keeps alive.
        #          It's neccessary to unsubscribe from redis to terminate it.
        redis_subscribe(
            callback=self.add_to_queue,
            pattern=settings.SUBMISSION_CHANNEL,
            redis=self.redis,
        )

        self.is_running = True
        Job(target=self.extraction, name='extraction').start()

        logger.info('Extractor started!')

    def stop(self):
        self.is_running = False
        # without this the redis thread will keep alive forever
        redis_unsubscribe(self.redis)
        logger.info('Extractor stopped!')

    def handle_pending_submissions(self, channel='*'):
        for key in get_redis_keys_by_pattern(channel, self.redis):
            self.add_to_queue(get_redis_subscribed_message(key=key, redis=self.redis))

    def add_to_queue(self, task):
        if task:
            self.pending_submissions.appendleft(task)

    def extraction(self):
        with PoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            while self.is_running:
                processes = []

                bulk_size = self._get_bulk_size(len(self.pending_submissions))
                for _ in range(bulk_size):
                    processes.append(
                        executor.submit(self.entity_extraction, self.pending_submissions.pop())
                    )

                for realm in self.extracted_entities.keys():
                    processes.append(
                        executor.submit(self.push_entities_to_kernel, realm)
                    )

                for realm in self.processed_submissions.keys():
                    processes.append(
                        executor.submit(self.push_submissions_to_kernel, realm)
                    )

                wait(processes, timeout=settings.CHECK_INTERVAL)

                # wait and check again later
                time.sleep(settings.CHECK_INTERVAL)

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
        while extracted_entities:
            current_entity_size = self._get_bulk_size(len(extracted_entities))
            entities = [
                extracted_entities.popleft()
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
        while processed_submissions:
            current_submission_size = self._get_bulk_size(len(processed_submissions))
            submissions = [
                processed_submissions.popleft()
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

            # wait and check again later
            time.sleep(settings.PUSH_TO_KERNEL_INTERVAL)

    def _add_to_tenant_queue(self, tenant, queue, element):
        try:
            queue[tenant].append(element)
        except KeyError:
            queue[tenant] = deque([element])

    def _get_bulk_size(self, size):
        return settings.MAX_BULK_SIZE if size > settings.MAX_BULK_SIZE else size
