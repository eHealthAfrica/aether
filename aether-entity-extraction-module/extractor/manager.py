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
import time
import concurrent.futures
import threading
import logging
from django.utils.translation import ugettext as _
from . import settings
from .utils import (
    get_from_redis_or_kernel,
    KERNEL_ARTEFACT_NAMES,
    kernel_data_request,
    remove_from_redis,
    get_redis_keys_by_pattern,
    get_redis_subcribed_message,
    redis_subscribe,
    redis_stop,
    MAX_WORKERS,
    SUBMISSION_EXTRACTION_FLAG,
    SUBMISSION_PAYLOAD_FIELD,
)

from aether.python.entity.extractor import (
    extract_create_entities,
    ENTITY_EXTRACTION_ERRORS,
    ENTITY_EXTRACTION_ENRICHMENT,
)

PUSH_TO_KERNEL_INTERVAL = 0.05
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class ExtractionManager():

    def __init__(self, redis=None):
        self.SUBMISSION_QUEUE = collections.deque()
        self.PROCESSED_SUBMISSIONS = collections.deque()
        self.PROCESSED_ENTITIES = collections.deque()
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
        redis_subscribe(
            callback=callback,
            pattern=channel,
            redis=self.redis
        )

    def handle_pending_submissions(self, channel='*'):
        pending_submission_keys = get_redis_keys_by_pattern(
            channel,
            self.redis
        )
        for key in pending_submission_keys:
            self.add_to_queue(get_redis_subcribed_message(
                key,
                self.redis
            ))

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
        current_submission['tenant'] = submission.tenant
        submission_entities = []
        mapping_ids = current_submission[KERNEL_ARTEFACT_NAMES.mappings]
        for mapping_id in mapping_ids:
            schemas = {}
            schema_decorators = {}
            mapping = get_from_redis_or_kernel(
                mapping_id,
                KERNEL_ARTEFACT_NAMES.mappings,
                submission.tenant,
                self.redis
            )
            if mapping and KERNEL_ARTEFACT_NAMES.schemadecorators in mapping:
                schemadecorator_ids = mapping[KERNEL_ARTEFACT_NAMES.schemadecorators]
                schema_decorators = mapping['definition']['entities']
                for shemadecorator_id in schemadecorator_ids:
                    sd = get_from_redis_or_kernel(
                        shemadecorator_id,
                        KERNEL_ARTEFACT_NAMES.schemadecorators,
                        submission.tenant,
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
                    current_submission[SUBMISSION_PAYLOAD_FIELD][ENTITY_EXTRACTION_ENRICHMENT] = \
                        submission_data[ENTITY_EXTRACTION_ENRICHMENT]
            except Exception as e:
                current_submission = self.flag_invalid_submission(
                    current_submission,
                    submission_data,
                    e
                )

        if ENTITY_EXTRACTION_ERRORS not in current_submission:
            current_submission[SUBMISSION_PAYLOAD_FIELD][ENTITY_EXTRACTION_ERRORS] = []
            current_submission[SUBMISSION_EXTRACTION_FLAG] = True
            [self.PROCESSED_ENTITIES.appendleft(entity) for entity in submission_entities]

        # add to processed submission queue
        self.PROCESSED_SUBMISSIONS.appendleft(current_submission)

    def flag_invalid_submission(self, submission, errors, excep):
        submission[SUBMISSION_PAYLOAD_FIELD][ENTITY_EXTRACTION_ERRORS] \
            += errors[ENTITY_EXTRACTION_ERRORS]
        submission[SUBMISSION_PAYLOAD_FIELD][ENTITY_EXTRACTION_ERRORS] += [_(str(excep))]
        return submission

    def process(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while self.SUBMISSION_QUEUE:
                executor.submit(self.entity_extraction, self.SUBMISSION_QUEUE.pop())
        if self.SUBMISSION_QUEUE:
            self.process()
        else:
            self.is_extracting = False

    def push_to_kernel(self):
        logger.debug('Pushing to kernel')
        while self.PROCESSED_ENTITIES or self.PROCESSED_SUBMISSIONS or self.is_extracting:
            current_entity_size = len(self.PROCESSED_ENTITIES)
            current_submission_size = len(self.PROCESSED_SUBMISSIONS)
            if current_entity_size:
                entities = [self.PROCESSED_ENTITIES.pop() for _ in range(current_entity_size)]
                # post to kernel entity
                try:
                    res = kernel_data_request(
                        url='entities/',
                        method='post',
                        data=entities,
                    )
                except Exception as e:
                    # todo: find a way to handle unsubmitted entities
                    logger.debug(str(e))

            if current_submission_size:
                submissions = [
                    self.PROCESSED_SUBMISSIONS.pop()
                    for _ in range(current_submission_size)
                ]

                # remove helper property
                submission_tenant = {}
                for submission in submissions:
                    submission_tenant[submission['id']] = submission['tenant']
                    submission.pop('tenant')
                    submission.pop('mappings')

                # post to kernel submissions
                try:
                    res = kernel_data_request(
                        url=f'submissions/bulk_update/',
                        method='patch',
                        data=submissions,
                    )

                    # remove submissions from redis
                    for s in res:
                        remove_from_redis(
                            s,
                            f'{KERNEL_ARTEFACT_NAMES.submissions}',
                            submission_tenant[s],
                            self.redis
                        )
                except Exception as e:
                    logger.debug(str(e))

            time.sleep(PUSH_TO_KERNEL_INTERVAL)
        self.is_pushing_to_kernel = False
        logger.debug('Pushed all entities and submissions to kernel')
