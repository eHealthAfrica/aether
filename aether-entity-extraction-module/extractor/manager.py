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

import sys
import time

from collections import defaultdict
from queue import Queue, Empty
import multiprocessing as mp
from threading import Thread

from typing import (
    Any, Callable, List
)

from requests.exceptions import HTTPError
from redis.exceptions import ConnectionError as RedisConnectionError
from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    extract_create_entities,
)

from extractor import settings
from extractor.utils import (
    ARTEFACT_NAMES,
    SUBMISSION_EXTRACTION_FLAG,
    SUBMISSION_PAYLOAD_FIELD,
    Artifact,
    cache_objects,
    count_quarantined,
    get_failed_objects,
    get_from_redis_or_kernel,
    get_redis_keys_by_pattern,
    get_redis_subscribed_message,
    kernel_data_request,
    quarantine,
    remove_from_cache,
    remove_from_redis,
    redis_subscribe,
)

logger = settings.get_logger('Manager')


class ExtractionManager():

    def __init__(self, redis=None):
        logger.debug(f'Manager Loading.')
        # save the submissions and entities by their realm
        # this is required to push them back to kernel
        self.stopped = False
        self.extraction_pool = mp.Pool()  # lots of power here
        self.kernel_comm_pool = mp.Pool(processes=1)  # only one concurrent request to Kernel.
        self.manager = mp.Manager()
        self.processed_submissions = self.manager.Queue()
        self.extracted_entities = self.manager.Queue()
        self.redis = redis
        # load failed from redis. When running will cycle back into
        # queue on failure.
        for _type in [Artifact.ENTITY, Artifact.SUBMISSION]:
            logger.info(f'{_type} #{count_quarantined(_type)} in quarantine')
        try:
            self.load_failed()
        except RedisConnectionError as err:
            logger.critical(f'Cannot connect to Redis. Fatal: {err}')
            sys.exit(1)
        # run the main worker loop in a new thread, no need to MP it.
        Thread(target=self.worker).start()
        logger.debug(f'Manager Ready.')

    def callback(self, result):
        logger.info(result)

    def load_failed(self):
        get_failed_objects(self.processed_submissions, Artifact.SUBMISSION)
        get_failed_objects(self.extracted_entities, Artifact.ENTITY)
        fc_sub = self.processed_submissions.qsize()
        fc_ent = self.extracted_entities.qsize()
        logger.info(f'Loaded failed: s:{fc_sub}, e:{fc_ent}')

    def get_prepared(self, queue, size=settings.MAX_PUSH_SIZE):
        res = defaultdict(list)
        for i in range(size):
            try:
                k, v = queue.get_nowait()
                res[k].append(v)
            except Empty:
                break
        return res

    def worker(self):
        while not self.stopped:
            logger.debug('Looking for work')
            read_subs = self.get_prepared(self.processed_submissions)
            if read_subs:
                count = sum([len(v) for v in read_subs.values()])
                logger.info(f'pushing Subs {count}')
                for k in read_subs.keys():
                    self.kernel_comm_pool.apply_async(
                        push_submissions_to_kernel,
                        (
                            k,
                            read_subs[k],
                            self.processed_submissions
                        ),
                        callback=cb_s)
            read_entities = self.get_prepared(self.extracted_entities)
            if read_entities:
                count = sum([len(v) for v in read_entities.values()])
                logger.info(f'pushing Ent {count}')
                for k in read_entities.keys():
                    self.kernel_comm_pool.apply_async(
                        push_entities_to_kernel,
                        (
                            k,
                            read_entities[k],
                            self.extracted_entities
                        ),
                        callback=cb_e)
            time.sleep(1)
        logger.info('Manager caught stop signal')

    def stop(self):
        print('stopping')
        self.stopped = True
        self.extraction_pool.close()
        self.kernel_comm_pool.close()
        self.extraction_pool.join()
        self.kernel_comm_pool.join()
        print('stopped')

    def subscribe_to_redis_channel(self, callback: callable, channel: str):
        redis_subscribe(callback=callback, pattern=channel, redis=self.redis)

    def handle_pending_submissions(self, channel='*'):
        for key in get_redis_keys_by_pattern(channel, self.redis):
            self.add_to_queue(get_redis_subscribed_message(key=key, redis=self.redis))

    def add_to_queue(self, task):
        if not task:
            logger.info('No task to enqueue')
            return
        # enqueue work
        self.extraction_pool.apply_async(
            entity_extraction,
            (
                task,
                self.extracted_entities,
                self.processed_submissions),
            callback=cb_ingress)


def entity_extraction(task, entity_queue, submission_queue):
    # receive task from redis
    # if not found on redis, get from kernel and cache on redis
    # if not found on kernel ==> flag submission as invalid and skip extraction
    logger.info(f'handling {task.id}')
    try:
        tenant = task.tenant
        submission = task.data
        payload = submission[SUBMISSION_PAYLOAD_FIELD]
        submission_entities = []
        logger.info(f'Got extraction Task: {task.id}')
        # extract entities for each linked mapping
        for mapping_id in submission[ARTEFACT_NAMES.mappings]:
            mapping = get_from_redis_or_kernel(
                id=mapping_id,
                model_type=ARTEFACT_NAMES.mappings,
                tenant=tenant
            )
            try:
                # get required artefacts
                schemas = {}
                schema_decorators = mapping['definition']['entities']
                for shemadecorator_id in mapping[ARTEFACT_NAMES.schemadecorators]:
                    sd = get_from_redis_or_kernel(
                        id=shemadecorator_id,
                        model_type=ARTEFACT_NAMES.schemadecorators,
                        tenant=tenant
                    )

                    schema_definition = None
                    if sd and ARTEFACT_NAMES.schema_definition in sd:
                        schema_definition = sd[ARTEFACT_NAMES.schema_definition]

                    elif sd and ARTEFACT_NAMES.schema_id in sd:
                        schema = get_from_redis_or_kernel(
                            id=sd[ARTEFACT_NAMES.schema_id],
                            model_type=ARTEFACT_NAMES.schemas,
                            tenant=settings.DEFAULT_REALM
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
                        'id': entity.payload['id'],
                        'payload': entity.payload,
                        'status': entity.status,
                        'schemadecorator': schema_decorators[entity.schemadecorator_name],
                        'submission': task.id,
                        'mapping': mapping_id,
                        'mapping_revision': mapping['revision'],
                    })

            except Exception as e:
                logger.error(f'Extraction error {e}')
                try:
                    payload[ENTITY_EXTRACTION_ERRORS].append(str(e))
                except KeyError:
                    payload[ENTITY_EXTRACTION_ERRORS] = [str(e)]

        is_extracted = False
        if not payload.get(ENTITY_EXTRACTION_ERRORS):
            payload.pop(ENTITY_EXTRACTION_ERRORS, None)
            is_extracted = True
            # Let's assume it's going to fail so we don't reextract if kernel
            # can't accept the results. Otherwise we'll get different IDs
            cache_objects(
                submission_entities,
                task.tenant,
                Artifact.ENTITY,
                entity_queue
            )
        # add to processed submission queue (but only the required fields)
        # Let's assume it's going to fail so we don't reextract if kernel
        # can't accept the results.
        cache_objects(
            [{
                'id': task.id,
                SUBMISSION_PAYLOAD_FIELD: payload,
                SUBMISSION_EXTRACTION_FLAG: is_extracted,
            }],
            task.tenant,
            Artifact.SUBMISSION,
            submission_queue
        )
        # remove original submissions from redis
        remove_from_redis(
            id=task.id,
            model_type=ARTEFACT_NAMES.submissions,
            tenant=task.tenant
        )
        logger.info(f'finished task {task.id}')
        return 1
    except Exception as err:
        logger.error(f'extractor ERROR!: {err}')
        return 0


def push_entities_to_kernel(realm, entities, entity_queue):
    if not entities:
        logger.info(f'Entities queue for realm {realm} was empty')
        return
    logger.info(f'Pushing #{len(entities)} chunk to {realm}')
    try:
        kernel_data_request(
            url='entities.json',
            method='post',
            data=entities,
            realm=realm,
        )
        logger.info(f'{len(entities)} accepted by {realm}')
        for i in entities:
            remove_from_cache(
                i,
                realm,
                Artifact.ENTITY
            )
        return len(entities)
    except HTTPError as e:
        return handle_kernel_errors(
            e,
            push_entities_to_kernel,
            entities,
            realm,
            Artifact.ENTITY,
            entity_queue
        )


def push_submissions_to_kernel(realm, submissions, submission_queue):
    if not submissions:
        logger.info(f'Submissions queue for realm {realm} was empty')
        return
    else:
        logger.info(f'popped {len(submissions)}')

    try:
        kernel_data_request(
            url='submissions/bulk_update_extracted.json',
            method='patch',
            data=submissions,
            realm=realm,
        )
        for submission in submissions:
            remove_from_cache(
                submission,
                realm,
                Artifact.SUBMISSION
            )
        return len(submissions)
    except HTTPError as e:
        return handle_kernel_errors(
            e,
            push_submissions_to_kernel,
            submissions,
            realm,
            Artifact.SUBMISSION,
            submission_queue
        )


def handle_kernel_errors(
    e: Exception,
    retry_fn: Callable,
    objs: List[Any],
    realm: str,
    _type: Artifact,
    queue: Queue
):
    _code = e.response.status_code
    BAD_REQUEST = _code == 400
    if not BAD_REQUEST:
        logger.error(_code)
    # if a small batch failed, cache it
    _size = len(objs)
    if _size > 1 and BAD_REQUEST:
        # break down big failures and retry parts
        # reducing by half each time
        _chunks = halve_iterable(objs, _size)
        logger.debug(f'Trying smaller chunks... than {_size}')
        return sum([
            retry_fn(
                realm, c, queue
            ) for c in _chunks
        ])
    elif BAD_REQUEST:
        for i in objs:
            remove_from_cache(
                i,
                realm,
                _type
            )
        quarantine(
            objs,
            realm,
            _type,
        )
        return 0
    else:
        logger.error(f'caching {_size} failed for {_code}')
        cache_objects(
            objs,
            realm,
            _type,
            queue
        )
        return 0


def halve_iterable(obj, _size):
    # chop
    _chunk_size = int(_size / 2) \
        if (_size / 2 == int(_size / 2)) \
        else int(_size / 2) + 1
    logger.debug(f'new chunk size {_chunk_size}')
    for i in range(0, len(obj), _chunk_size):
        yield obj[i:i + _chunk_size]


total_arrived = 0
total_cut = 0
total_sent = 0


def cb_ingress(result):
    global total_arrived
    total_arrived += int(result)
    logger.debug(['IN', result, total_arrived])


def cb_s(result):
    global total_cut
    total_cut += int(result)
    logger.debug(['O-SUB', result, total_cut])


def cb_e(result):
    global total_sent
    total_sent += int(result)
    logger.debug(['O-ENT', result, total_sent])
