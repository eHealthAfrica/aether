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
import concurrent.futures
import logging
import threading
import time

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    ENTITY_EXTRACTION_ENRICHMENT,
    extract_create_entities,
)

from extractor import settings
from extractor.utils import (
    KERNEL_ARTEFACT_NAMES,
    SUBMISSION_EXTRACTION_FLAG,
    SUBMISSION_PAYLOAD_FIELD,

    cache_failed_entities,
    get_from_redis_or_kernel,
    get_redis_keys_by_pattern,
    get_redis_subscribed_message,
    kernel_data_request,
    remove_from_redis,
    redis_subscribe,
    redis_stop,
)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class ExtractionManager():

    def __init__(self, redis=None):
        self.SUBMISSION_QUEUE = collections.deque()
        self.PROCESSED_SUBMISSIONS = collections.deque()

        self.realm_entities = {}
        self.is_extracting = False
        self.is_pushing_to_kernel = False
        self.redis = redis
        self.push_to_kernel_thread = None
        self.extraction_thread = None
        self.start_time = None
        self.end_time = None

    def stop(self):
        redis_stop(self.redis)
        self.is_extracting = False
        self.is_pushing_to_kernel = False

    def subscribe_to_redis_channel(self, callback: callable, channel: str):
        redis_subscribe(callback=callback, pattern=channel, redis=self.redis)

    def handle_pending_submissions(self, channel='*'):
        for key in get_redis_keys_by_pattern(channel, self.redis):
            self.add_to_queue(get_redis_subscribed_message(key, self.redis))

    def add_to_queue(self, submission):
        if submission:
            self.SUBMISSION_QUEUE.appendleft(submission)
            if not self.is_extracting:
                self.is_extracting = True
                self.extraction_thread = threading.Thread(
                    target=self.process,
                    name='extraction-thread'
                )
                self.extraction_thread.start()

            if not self.is_pushing_to_kernel:
                self.is_pushing_to_kernel = True
                self.push_to_kernel_thread = threading.Thread(
                    target=self.push_to_kernel,
                    name='push-to-kernel-thread'
                )
                self.push_to_kernel_thread.start()

    def entity_extraction(self, submission):
        # get artifacts from redis
        # if not found on redis, get from kernel and cache on redis
        # if not found on kernel ==> flag submission as invalid and skip extraction

        current_submission = submission.data
        current_payload = current_submission[SUBMISSION_PAYLOAD_FIELD]
        current_tenant = submission.tenant

        current_submission['tenant'] = current_tenant
        submission_entities = []

        mapping_ids = current_submission[KERNEL_ARTEFACT_NAMES.mappings]
        for mapping_id in mapping_ids:
            schemas = {}
            schema_decorators = {}
            mapping = get_from_redis_or_kernel(
                mapping_id,
                KERNEL_ARTEFACT_NAMES.mappings,
                current_tenant,
                self.redis
            )

            if mapping and KERNEL_ARTEFACT_NAMES.schemadecorators in mapping:
                schemadecorator_ids = mapping[KERNEL_ARTEFACT_NAMES.schemadecorators]
                schema_decorators = mapping['definition']['entities']
                for shemadecorator_id in schemadecorator_ids:
                    sd = get_from_redis_or_kernel(
                        shemadecorator_id,
                        KERNEL_ARTEFACT_NAMES.schemadecorators,
                        current_tenant,
                        self.redis
                    )

                    schema_definition = None
                    if sd and KERNEL_ARTEFACT_NAMES.schema_definition in sd:
                        schema_definition = sd[KERNEL_ARTEFACT_NAMES.schema_definition]
                    elif sd and KERNEL_ARTEFACT_NAMES.single_schema in sd:
                        schema = get_from_redis_or_kernel(
                            sd[KERNEL_ARTEFACT_NAMES.single_schema],
                            KERNEL_ARTEFACT_NAMES.schemas,
                            settings.DEFAULT_REALM,
                            self.redis
                        )
                        if schema and schema['definition']:
                            schema_definition = schema['definition']

                    if schema_definition:
                        schemas[sd['name']] = schema_definition

            # perform entity extraction
            try:
                submission_data, entities = extract_create_entities(
                    submission_payload=submission.data['payload'],
                    mapping_definition=mapping['definition'],
                    schemas=schemas,
                )

                for entity in entities:
                    schemadecorator_name = entity.schemadecorator_name
                    schemadecorator = schema_decorators[schemadecorator_name]
                    submission_entities.append({
                        'payload': entity.payload,
                        'status': entity.status,
                        'schemadecorator': schemadecorator,
                        'submission': submission.id,
                        'mapping': mapping_id,
                        'mapping_revision': mapping['revision'],
                    })

                if ENTITY_EXTRACTION_ENRICHMENT in submission_data:
                    current_payload[ENTITY_EXTRACTION_ENRICHMENT] = \
                        submission_data[ENTITY_EXTRACTION_ENRICHMENT]

            except Exception as e:
                current_payload[ENTITY_EXTRACTION_ERRORS] = current_payload.get(ENTITY_EXTRACTION_ERRORS, [])
                current_payload[ENTITY_EXTRACTION_ERRORS].append(str(e))

        if not current_payload.get(ENTITY_EXTRACTION_ERRORS):
            current_payload.pop(ENTITY_EXTRACTION_ERRORS, None)
            current_submission[SUBMISSION_EXTRACTION_FLAG] = True
            for entity in submission_entities:
                try:
                    self.realm_entities[current_tenant].append(entity)
                except KeyError:
                    self.realm_entities[current_tenant] = collections.deque([entity])

        # add to processed submission queue
        self.PROCESSED_SUBMISSIONS.appendleft(current_submission)

    def process(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
            while self.SUBMISSION_QUEUE:
                executor.submit(self.entity_extraction, self.SUBMISSION_QUEUE.pop())
        if self.SUBMISSION_QUEUE:
            self.process()
        else:
            self.is_extracting = False

    def realm_has_entities(self):
        for realm in self.realm_entities:
            if self.realm_entities[realm]:
                return True
        return False

    def push_to_kernel(self):
        def _get_size(size):
            return settings.MAX_PUSH_SIZE if size > settings.MAX_PUSH_SIZE else size

        logger.debug('Pushing to kernel')
        while self.realm_has_entities() or self.PROCESSED_SUBMISSIONS or self.is_extracting:
            current_submission_size = _get_size(len(self.PROCESSED_SUBMISSIONS))

            for realm in self.realm_entities:
                current_entity_size = _get_size(len(self.realm_entities[realm]))
                if current_entity_size:
                    entities = [self.realm_entities[realm].pop() for _ in range(current_entity_size)]
                    # post entities to kernel per realm
                    try:
                        kernel_data_request(
                            url='entities/',
                            method='post',
                            data=entities,
                            realm=realm
                        )
                    except Exception as e:
                        logger.error(str(e))
                        # cache failed entities on redis for retries later
                        cache_failed_entities(entities, realm)

            if current_submission_size:
                submissions = [
                    self.PROCESSED_SUBMISSIONS.pop()
                    for _ in range(current_submission_size)
                ]
                submission_tenant = {}

                # remove helper properties
                for submission in submissions:
                    submission_tenant[submission['id']] = submission['tenant']
                    submission.pop('tenant', None)
                    submission.pop('mappings', None)

                # post to kernel submissions
                try:
                    submission_ids = kernel_data_request(
                        url='submissions/bulk_update_extracted/',
                        method='patch',
                        data=submissions,
                    )
                    # remove submissions from redis
                    for submission_id in submission_ids:
                        remove_from_redis(
                            submission_id,
                            f'{KERNEL_ARTEFACT_NAMES.submissions}',
                            submission_tenant[submission_id],
                            self.redis
                        )
                except Exception as e:
                    logger.error(str(e))

            time.sleep(settings.PUSH_TO_KERNEL_INTERVAL)

        self.is_pushing_to_kernel = False
        logger.debug('Pushed all entities and submissions to kernel')
