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

from datetime import datetime
import signal
import sys
import time
import traceback
from uuid import uuid4

from collections import defaultdict
from queue import Queue, Empty
import multiprocessing as mp
from threading import Thread

from typing import Any, Dict, List

from requests.exceptions import HTTPError
from redis.exceptions import LockError, ConnectionError as RedisConnectionError

from aether.python.redis.task import Task
from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    extract_create_entities,
)

from extractor import settings, utils

MAPPINSET_FIELD = 'mappingset'
SUBMISSION_EXTRACTION_FLAG = 'is_extracted'
SUBMISSION_PAYLOAD_FIELD = 'payload'
SUBMISSION_ENTITIES_FIELD = 'extracted_entities'


_logger = settings.get_logger('Manager')


class ExtractionManager():
    LOCK_TYPE = '_aether-extraction-manager_lock'
    kernel_comm_pool: mp.Pool = None
    extraction_pool: mp.Pool = None
    processed_submissions: Queue = None
    manager: mp.Manager = None

    def __init__(self, channel=settings.SUBMISSION_CHANNEL):
        self._id = f'{str(uuid4())}-{str(datetime.now().isoformat())}'
        self.redis = utils.REDIS_HANDLER.get_redis()
        self.task_helper = utils.REDIS_HANDLER.get_helper()
        self.channel = channel
        self.stopped = True
        self.manager = mp.Manager()
        self._start_pools()

    def start(self):
        if not self.stopped:
            raise RuntimeError('Manager already started!')
        self.worker_thread = Thread(target=self.worker, daemon=False)
        self._start_pools()
        _logger.info(f'starting with ID: {self._id}')

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        # start jobs
        self.stopped = False

        # run the main worker loop in a new thread, no need to MP it.
        self.worker_thread.start()

        # Report on permanently failed submissions
        # (Failed with 400 Bad Request)
        _logger.info(f'#{utils.count_quarantined()} submissions in quarantine')

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
        Thread(target=self.__stop_on_exit, daemon=False).start()

    def __stop_on_exit(self):
        self.worker_thread.join()
        _logger.info('Worker complete, stopping other processes')
        try:
            self.stop()
        except RuntimeError:
            _logger.debug('Already stopped')

    def _start_pools(self):
        if not self.processed_submissions:
            self.processed_submissions = self.manager.Queue()
        if not self.extraction_pool:
            self.extraction_pool = mp.Pool()
        # only one concurrent request to Kernel.
        if not self.kernel_comm_pool:
            self.kernel_comm_pool = mp.Pool(processes=1)

    def _get_lock(self, timeout=settings.LOCK_TIMEOUT, token=None):
        try:
            _lock = self.redis.lock(
                self.LOCK_TYPE,                         # same ID across all
                timeout=60,                             # TTL in redis
                blocking_timeout=timeout)               # attempt for this long
            if not _lock.acquire(token=token or self.LOCK_TYPE):
                raise LockError('Could not get lock')
            # update lock_info
            _meta = self.task_helper.add(
                {'id': 'lockmeta', 'owner': self._id}, self.LOCK_TYPE, '_all')
            return _lock
        except LockError as ler:
            _meta = self.task_helper.get('lockmeta', self.LOCK_TYPE, '_all')
            _logger.error(f'Could not acquire lock, owned by {_meta}')
            raise ler

    def stop(self, *args, **kwargs):
        if self.stopped:
            raise RuntimeError('Manager not running!')

        _logger.info('stopping')

        # indicate the thread to stop
        self.stopped = True

        utils.redis_unsubscribe()

        # do not allow new entries
        self.extraction_pool.close()
        self.kernel_comm_pool.close()

        # let the current jobs finish
        self.extraction_pool.join()
        self.kernel_comm_pool.join()
        self.worker_thread.join()
        self.processed_submissions = None
        self.kernel_comm_pool = None
        self.worker_thread = None
        _logger.info('stopped')

    def is_alive(self):
        return not self.stopped

    def worker(self):
        try:
            _lock = self._get_lock()
            while not self.stopped:
                _logger.debug(f'Looking for work: {self._id}')
                _lock.reacquire()
                read_subs = get_prepared(self.processed_submissions)
                for realm, objs in read_subs.items():
                    self.kernel_comm_pool.apply_async(
                        func=push_to_kernel,
                        args=(
                            realm,
                            objs,
                            self.processed_submissions,
                        ))

                time.sleep(settings.WAIT_INTERVAL)
            _logger.info('Manager caught stop signal')
        except LockError as ler:
            _logger.error(f'Could not acquire lock in {settings.LOCK_TIMEOUT}; {ler}')
        except Exception as err:
            _logger.error(f'Worker died with err: {err}')
            _logger.info(traceback.format_exc())
        finally:
            try:
                _lock.release()
            except (UnboundLocalError, LockError) as aer:
                _logger.warning(f'error releasing lock: {aer}')
            _logger.info(f'Worker stopped {self._id}')

    def load_failed(self) -> None:
        utils.get_failed_objects(self.processed_submissions)
        fc_sub = self.processed_submissions.qsize()
        _logger.info(f'Loaded failed: {fc_sub}')
        if fc_sub:
            _logger.info(utils.list_failed_objects())

    def subscribe_to_channel(self):
        # include current submissions from redis
        _logger.info(f'Subscribing to {self.channel}')
        for key in utils.get_redis_keys_by_pattern(self.channel):
            _logger.debug(f'Picking up missed message from {self.channel} with key: {key}')
            self.add_to_queue(utils.get_redis_subscribed_message(key=key))

        # subscribe to new submissions
        utils.redis_subscribe(callback=self.add_to_queue, pattern=self.channel)

    def add_to_queue(self, task: Task) -> bool:
        if not isinstance(task, Task):
            return False
        _logger.debug(f'Adding Task with ID {task.id} to extraction pool')
        self.extraction_pool.apply_async(
            func=entity_extraction,
            args=(
                task,
                self.processed_submissions,
            )
        )
        return True


def entity_extraction(task, submission_queue):
    # receive task from redis
    # if artifacts found on redis, get from kernel and cache on redis
    # if artifacts not found on kernel ==> flag submission as invalid and skip extraction

    try:
        tenant = task.tenant
        submission = task.data
        payload = submission[SUBMISSION_PAYLOAD_FIELD]
        submission_entities = []
        _logger.info(f'Got extraction Task: {task.id}')

        # extract entities for each linked mapping
        mappingset_id = None  # same for each mapping on a single submission
        for mapping_id in submission[utils.ARTEFACT_NAMES.mappings]:
            mapping = utils.get_from_redis_or_kernel(
                id=mapping_id,
                model_type=utils.ARTEFACT_NAMES.mappings,
                tenant=tenant
            )
            if not mapping:
                mappingset_id = None
                raise ValueError(f'Mapping {mapping_id} not found.')
            else:
                mappingset_id = mapping['mappingset']

            # get required artefacts
            schemas = {}
            schema_decorators = mapping['definition']['entities']
            for schemadecorator_id in mapping[utils.ARTEFACT_NAMES.schemadecorators]:
                sd = utils.get_from_redis_or_kernel(
                    id=schemadecorator_id,
                    model_type=utils.ARTEFACT_NAMES.schemadecorators,
                    tenant=tenant
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

        if not payload.get(ENTITY_EXTRACTION_ERRORS):
            payload.pop(ENTITY_EXTRACTION_ERRORS, None)
            is_extracted = True
        else:
            submission_entities.clear()
            is_extracted = False

        # add to processed submission queue (but only the required fields)
        processed_submission = {
            'id': task.id,
            MAPPINSET_FIELD: mappingset_id,
            SUBMISSION_PAYLOAD_FIELD: payload,
            SUBMISSION_EXTRACTION_FLAG: is_extracted,
            SUBMISSION_ENTITIES_FIELD: submission_entities,
        }
        _logger.debug(f'finished task {task.id}')
        return 1

    except Exception as err:
        _logger.info(f'extractor error: {err}')
        processed_submission = {
            'id': task.id,
            MAPPINSET_FIELD: mapping['mappingset'],
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
        )
        utils.remove_from_redis(
            id=task.id,
            model_type=utils.ARTEFACT_NAMES.submissions,
            tenant=task.tenant,
        )


def get_prepared(queue: Queue) -> Dict[str, Dict]:
    res = defaultdict(list)
    for _ in range(settings.MAX_PUSH_SIZE):
        try:
            realm, msg = queue.get_nowait()
            res[realm].append(msg)
        except Empty:
            break

    return res


def push_to_kernel(realm: str, objs: List[Any], queue: Queue):
    if not objs:
        _logger.debug('Nothing to send to kernel')
        return 0
    try:
        utils.kernel_data_request(url='submissions.json', method='patch', data=objs, realm=realm)
        for obj in objs:
            utils.remove_from_cache(obj, realm)
            utils.remove_from_quarantine(obj, realm)
        _logger.debug(f'submitted: {len(objs)} for {realm}')
        return len(objs)
    except HTTPError as e:
        _logger.debug(f'Kernel submission failed: {e.response.status_code}')
        _logger.debug(f'bad data: {objs}')
        if e.response.status_code == 400:
            if hasattr(e.response, 'text'):
                _logger.warning(f'Bad request: {e.response.text}')
            return handle_kernel_errors(objs, realm, queue)
        else:
            _logger.warning(f'Unexpected HTTP Status from Kernel: {e.response.status_code}')
            if hasattr(e.response, 'text'):
                _logger.info(f'Unexpected Response from Kernel: {e.response.text}')
            utils.cache_objects(objs, realm, queue)
            return 0
    except Exception as err:
        _logger.critical(f'Unexpected error submitting to kernel {err}')


def handle_kernel_errors(objs: List[Any], realm: str, queue: Queue):
    _size = len(objs)
    if _size > 1:
        # break down big failures and retry parts
        # reducing by half each time
        _chunks = utils.halve_iterable(objs)
        _logger.debug(f'Trying smaller chunks than {_size}...')
        return sum([push_to_kernel(realm, chunk, queue) for chunk in _chunks])

    # Move bad object from cache to quarantine
    for obj in objs:
        utils.remove_from_cache(obj, realm)
    utils.quarantine(objs, realm)
    return 0
