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

import signal
import sys
import time

from collections import defaultdict
from queue import Queue, Empty
import multiprocessing as mp
from threading import Thread

from typing import (
    Any, Callable, Dict, List
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
    CacheType,
    cache_has_object,
    cache_objects,
    count_quarantined,
    get_failed_objects,
    get_from_redis_or_kernel,
    get_redis,
    get_redis_keys_by_pattern,
    get_redis_subscribed_message,
    halve_iterable,
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
        # Report on permanently failed submissions / entities
        # (Failed with 400 Bad Request)
        for _type in [Artifact.ENTITY, Artifact.SUBMISSION]:
            logger.info(f'{_type} #{count_quarantined(_type)} in quarantine')
        # load failed from redis. When running will cycle back into
        # queue on failure.
        try:
            self.load_failed()
        except RedisConnectionError as err:
            logger.critical(f'Cannot connect to Redis. Fatal: {err}')
            sys.exit(1)
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        # run the main worker loop in a new thread, no need to MP it.
        self.worker_thread = Thread(target=self.worker)
        self.worker_thread.start()
        logger.debug(f'Manager Ready.')

    def callback(self, result):
        logger.info(result)

    def load_failed(self) -> None:
        get_failed_objects(self.processed_submissions, Artifact.SUBMISSION)
        get_failed_objects(self.extracted_entities, Artifact.ENTITY)
        fc_sub = self.processed_submissions.qsize()
        fc_ent = self.extracted_entities.qsize()
        logger.info(f'Loaded failed: s:{fc_sub}, e:{fc_ent}')

    def worker(self):
        while not self.stopped:
            logger.debug('Looking for work')
            read_subs = get_prepared(
                self.processed_submissions,
                Artifact.SUBMISSION)
            if read_subs:
                count = sum([len(v) for v in read_subs.values()])
                logger.info(f'Publishing Updated Subs: {count}')
                for realm in read_subs.keys():
                    self.kernel_comm_pool.apply_async(
                        push_to_kernel,
                        (
                            Artifact.SUBMISSION,
                            realm,
                            read_subs[realm],
                            self.processed_submissions
                        ))
            read_entities = get_prepared(
                self.extracted_entities,
                Artifact.ENTITY)
            if read_entities:
                count = sum([len(v) for v in read_entities.values()])
                logger.info(f'Publishing Updated Entities {count}')
                for realm in read_entities.keys():
                    self.kernel_comm_pool.apply_async(
                        push_to_kernel,
                        (
                            Artifact.ENTITY,
                            realm,
                            read_entities[realm],
                            self.extracted_entities
                        ))
            time.sleep(1)
        logger.info('Manager caught stop signal')

    def stop(self, *args, **kwargs):
        logger.info('stopping')
        self.stopped = True
        self.extraction_pool.close()
        self.kernel_comm_pool.close()
        get_redis().stop()
        self.extraction_pool.join()
        self.kernel_comm_pool.join()
        self.worker_thread.join()
        logger.info('stopped')
        # sys.exit(0)

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
                self.processed_submissions))


def get_prepared(
    queue: Queue,
    _type: Artifact,
    size=settings.MAX_PUSH_SIZE
) -> Dict[str, Dict]:
    res = defaultdict(list)
    excluded = []
    for i in range(size):
        try:
            realm, msg = queue.get_nowait()
            if _type is Artifact.ENTITY:
                # check to see if the related submission has been sent off.
                sub_id = msg.get('submission')
                _cache_found = cache_has_object(sub_id, realm, Artifact.SUBMISSION)
                if _cache_found is CacheType.NORMAL:
                    logger.debug(f'Ignoring entity {msg.get("id")};'
                                 ' submission {sub_id} not sent')
                    excluded.append(tuple([realm, msg]))
                    continue
                elif _cache_found is CacheType.QUARANTINE:
                    logger.debug(f'Sending entity to Quarantine;'
                                 ' associated with bad sub {sub_id}')
                    quarantine([msg], realm, Artifact.ENTITY)
            res[realm].append(msg)
        except Empty:
            break
    for item in excluded:
        queue.put(item)
    return res


def entity_extraction(task, entity_queue, submission_queue):
    # receive task from redis
    # if artifacts found on redis, get from kernel and cache on redis
    # if artifacts not found on kernel ==> flag submission as invalid and skip extraction
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
        logger.debug(f'finished task {task.id}')
        return 1
    except Exception as err:
        logger.error(f'extractor ERROR!: {err}')
        return 0


def push_to_kernel(
    _type: Artifact,
    realm: str,
    objs: List[Any],
    queue: Queue
):
    if not objs:
        return 0
    if _type is Artifact.SUBMISSION:
        url = 'submissions/bulk_update_extracted.json'
        method = 'patch'
    elif _type is Artifact.ENTITY:
        url = 'entities.json'
        method = 'post'
    try:
        kernel_data_request(
            url=url,
            method=method,
            data=objs,
            realm=realm,
        )
        for obj in objs:
            remove_from_cache(
                obj,
                realm,
                _type
            )
        return len(objs)
    except HTTPError as e:
        return handle_kernel_errors(
            e,
            push_to_kernel,
            objs,
            realm,
            _type,
            queue
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
    # if a small batch failed, cache it
    _size = len(objs)
    if _size > 1 and BAD_REQUEST:
        # break down big failures and retry parts
        # reducing by half each time
        _chunks = halve_iterable(objs, _size)
        logger.debug(f'Trying smaller chunks... than {_size}')
        return sum([
            retry_fn(
                _type, realm, c, queue
            ) for c in _chunks
        ])
    elif BAD_REQUEST:
        # Move bad object from cache to quarantine
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
        logger.error('Unexpected HTTP Status from Kernel: {_code}')
        logger.error(f'caching {_size} failed for {_code}')
        cache_objects(
            objs,
            realm,
            _type,
            queue
        )
        return 0
