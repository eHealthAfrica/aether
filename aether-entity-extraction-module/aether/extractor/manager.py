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

import gevent
import signal
import sys

from collections import defaultdict
from queue import Queue, Empty
import multiprocessing as mp
from threading import Thread

from typing import Any, Dict, List

from requests.exceptions import HTTPError
from redis.exceptions import ConnectionError as RedisConnectionError

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    extract_create_entities,
)

from aether.extractor import settings, utils

SUBMISSION_EXTRACTION_FLAG = 'is_extracted'
SUBMISSION_PAYLOAD_FIELD = 'payload'
SUBMISSION_ENTITIES_FIELD = 'extracted_entities'


_logger = settings.get_logger('Manager')


class ExtractionManager():

    def __init__(self, redis=None, channel=settings.SUBMISSION_CHANNEL):
        self.redis = redis
        self.channel = channel

        self.stopped = True

        self.extraction_pool = mp.Pool()
        # only one concurrent request to Kernel.
        self.kernel_comm_pool = mp.Pool(processes=1)

        self.manager = mp.Manager()
        self.processed_submissions = self.manager.Queue()

        self.worker_thread = Thread(target=self.worker, daemon=True)
        self.pull_thread = Thread(target=self.pull, daemon=True)

    def start(self):
        if not self.stopped:
            raise RuntimeError('Manager already started!')

        _logger.info('starting')

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        gevent.signal_handler(signal.SIGTERM, self.stop)

        # start jobs
        self.stopped = False

        # run the main worker loop in a new thread, no need to MP it.
        self.worker_thread.start()
        self.pull_thread.start()

        # Report on permanently failed submissions
        # (Failed with 400 Bad Request)
        _logger.info(f'#{utils.count_quarantined(self.redis)} submissions in quarantine')

        # load failed from redis. When running will cycle back into
        # queue on failure.
        try:
            self.load_failed()
        except RedisConnectionError as err:  # pragma: no cover
            _logger.critical(f'Cannot connect to Redis. Fatal: {err}')
            sys.exit(1)

        # subscribe to redis channel
        self.subscribe_to_channel()

        _logger.info('started')

    def stop(self, *args, **kwargs):
        if self.stopped:
            raise RuntimeError('Manager not running!')

        _logger.info('stopping')

        # indicate the thread to stop
        self.stopped = True

        utils.redis_unsubscribe(self.redis)

        # do not allow new entries
        self.extraction_pool.close()
        self.kernel_comm_pool.close()

        # let the current jobs finish
        self.extraction_pool.join()
        self.kernel_comm_pool.join()
        self.worker_thread.join()
        self.pull_thread.join()

        _logger.info('stopped')

    def is_alive(self):
        return not self.stopped

    def worker(self):
        while not self.stopped:
            _logger.debug('Looking for work')

            read_subs = get_prepared(self.processed_submissions, self.redis)
            for realm, objs in read_subs.items():
                self.kernel_comm_pool.apply_async(
                    func=push_to_kernel,
                    args=(
                        realm,
                        objs,
                        self.processed_submissions,
                        self.redis,
                    ))

            self.safe_sleep(settings.WAIT_INTERVAL)

        _logger.info('Manager caught stop signal')

    def pull(self):
        while not self.stopped:
            _logger.debug('Looking for missing work')

            try:
                utils.kernel_data_request(url=settings.PULL_ENDPOINT, method='post')
            except Exception:
                _logger.warning('Could not access kernel to get missing work')

            self.safe_sleep(settings.PULL_INTERVAL)

        _logger.info('Manager caught stop signal')

    def load_failed(self) -> None:
        utils.get_failed_objects(self.processed_submissions, self.redis)
        fc_sub = self.processed_submissions.qsize()
        _logger.info(f'Loaded failed: {fc_sub}')

    def subscribe_to_channel(self):
        # include current submissions from redis
        for key in utils.get_redis_keys_by_pattern(self.channel, self.redis):
            self.add_to_queue(utils.get_redis_subscribed_message(key=key, redis=self.redis))

        # subscribe to new submissions
        utils.redis_subscribe(callback=self.add_to_queue, pattern=self.channel, redis=self.redis)

    def add_to_queue(self, task):
        self.extraction_pool.apply_async(
            func=entity_extraction,
            args=(
                task,
                self.processed_submissions,
                self.redis,
            )
        )

    def safe_sleep(self, dur):
        # keeps shutdown time low by yielding during sleep and checking if stopped.
        for x in range(int(dur * 10)):
            if not self.stopped:
                gevent.sleep(0.1)


def entity_extraction(task, submission_queue, redis=None):
    # receive task from redis
    # if artifacts found on redis, get from kernel and cache on redis
    # if artifacts not found on kernel ==> flag submission as invalid and skip extraction
    if not hasattr(task, 'data'):
        return

    try:
        tenant = task.tenant
        submission = task.data
        payload = submission[SUBMISSION_PAYLOAD_FIELD]
        submission_entities = []
        _logger.info(f'Got extraction Task: {task.id}')

        # extract entities for each linked mapping
        for mapping_id in submission[utils.ARTEFACT_NAMES.mappings]:
            mapping = utils.get_from_redis_or_kernel(
                id=mapping_id,
                model_type=utils.ARTEFACT_NAMES.mappings,
                tenant=tenant,
                redis=redis,
            )
            if not mapping:
                raise ValueError(f'Mapping {mapping_id} not found.')

            # get required artefacts
            schemas = {}
            schema_decorators = mapping['definition']['entities']
            for schemadecorator_id in schema_decorators.values():
                sd = utils.get_from_redis_or_kernel(
                    id=schemadecorator_id,
                    model_type=utils.ARTEFACT_NAMES.schemadecorators,
                    tenant=tenant,
                    redis=redis,
                )
                if not sd:
                    raise ValueError(f'No schemadecorator with ID {schemadecorator_id} found')

                schema_definition = None
                if sd and utils.ARTEFACT_NAMES.schema_definition in sd:
                    schema_definition = sd[utils.ARTEFACT_NAMES.schema_definition]

                elif sd and utils.ARTEFACT_NAMES.schema_id in sd:
                    schema = utils.get_from_redis_or_kernel(
                        id=sd[utils.ARTEFACT_NAMES.schema_id],
                        model_type=utils.ARTEFACT_NAMES.schemas,
                        tenant=settings.DEFAULT_REALM,
                        redis=redis,
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

        if not payload.get(ENTITY_EXTRACTION_ERRORS):
            payload.pop(ENTITY_EXTRACTION_ERRORS, None)
            is_extracted = True
        else:
            submission_entities.clear()
            is_extracted = False

        # add to processed submission queue (but only the required fields)
        processed_submission = {
            'id': task.id,
            SUBMISSION_PAYLOAD_FIELD: payload,
            SUBMISSION_EXTRACTION_FLAG: is_extracted,
            SUBMISSION_ENTITIES_FIELD: submission_entities,
        }
        _logger.info(f'finished task {task.id}')
        return 1

    except Exception as err:
        _logger.info(f'extraction error on task {task.id}: {err}')
        processed_submission = {
            'id': task.id,
            SUBMISSION_PAYLOAD_FIELD: {
                **payload,
                ENTITY_EXTRACTION_ERRORS: [str(err)],
            },
            SUBMISSION_EXTRACTION_FLAG: False,
        }
        return 0

    finally:
        # Let's assume it's going to fail so we don't reextract if kernel
        # can't accept the results.
        utils.cache_objects(
            objects=[processed_submission],
            realm=task.tenant,
            queue=submission_queue,
            redis=redis,
        )
        utils.remove_from_redis(
            id=task.id,
            model_type=utils.ARTEFACT_NAMES.submissions,
            tenant=task.tenant,
            redis=redis,
        )


def get_prepared(queue: Queue, redis=None) -> Dict[str, Dict]:
    res = defaultdict(list)
    for _ in range(settings.MAX_PUSH_SIZE):
        try:
            realm, msg = queue.get_nowait()
            res[realm].append(msg)
        except Empty:
            break

    return res


def push_to_kernel(realm: str, objs: List[Any], queue: Queue, redis=None):
    if not objs:
        return 0

    try:
        utils.kernel_data_request(url='submissions.json', method='patch', data=objs, realm=realm)
        for obj in objs:
            utils.remove_from_cache(obj, realm, redis)
            utils.remove_from_quarantine(obj, realm, redis)
        return len(objs)
    except HTTPError as e:
        if e.response.status_code == 400:
            return handle_kernel_errors(objs, realm, queue, redis)
        else:
            _logger.warning(f'Unexpected HTTP Status from Kernel: {e.response.status_code}')
            utils.cache_objects(objs, realm, queue, redis)
            return 0


def handle_kernel_errors(objs: List[Any], realm: str, queue: Queue, redis=None):
    _size = len(objs)
    if _size > 1:
        # break down big failures and retry parts
        # reducing by half each time
        _chunks = utils.halve_iterable(objs)
        _logger.debug(f'Trying smaller chunks than {_size}...')
        return sum([push_to_kernel(realm, chunk, queue, redis) for chunk in _chunks])

    # Move bad object from cache to quarantine
    for obj in objs:
        utils.remove_from_cache(obj, realm, redis)
    utils.quarantine(objs, realm, redis)
    return 0
