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

from typing import Any, Dict, List

from requests.exceptions import HTTPError
from redis.exceptions import ConnectionError as RedisConnectionError

from aether.python.entity.extractor import (
    ENTITY_EXTRACTION_ERRORS,
    extract_create_entities,
)

from extractor import settings, utils

SUBMISSION_EXTRACTION_FLAG = 'is_extracted'
SUBMISSION_PAYLOAD_FIELD = 'payload'

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
        self.extracted_entities = self.manager.Queue()

        self.worker_thread = Thread(target=self.worker, daemon=True)

    def start(self):
        _logger.info('starting')

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        # start jobs
        self.stopped = False

        # Report on permanently failed submissions / entities
        # (Failed with 400 Bad Request)
        for _type in [utils.Artifact.ENTITY, utils.Artifact.SUBMISSION]:
            _logger.info(f'{_type} #{utils.count_quarantined(_type)} in quarantine')

        # load failed from redis. When running will cycle back into
        # queue on failure.
        try:
            self.load_failed()
        except RedisConnectionError as err:
            _logger.critical(f'Cannot connect to Redis. Fatal: {err}')
            sys.exit(1)

        # run the main worker loop in a new thread, no need to MP it.
        self.worker_thread.start()

        # subscribe to redis channel
        self.subscribe_to_channel()

        _logger.info('started')

    def stop(self, *args, **kwargs):
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
        if self.worker_thread.is_alive():
            self.worker_thread.join()

        _logger.info('stopped')

    def is_alive(self):
        return not self.stopped

    def load_failed(self) -> None:
        utils.get_failed_objects(self.processed_submissions, utils.Artifact.SUBMISSION, self.redis)
        utils.get_failed_objects(self.extracted_entities, utils.Artifact.ENTITY, self.redis)

        fc_sub = self.processed_submissions.qsize()
        fc_ent = self.extracted_entities.qsize()
        _logger.info(f'Loaded failed: s:{fc_sub}, e:{fc_ent}')

    def worker(self):
        while not self.stopped:
            _logger.debug('Looking for work')

            read_subs = get_prepared(self.processed_submissions, utils.Artifact.SUBMISSION, self.redis)
            if read_subs:
                for realm in read_subs.keys():
                    self.kernel_comm_pool.apply_async(
                        func=push_to_kernel,
                        args=(
                            utils.Artifact.SUBMISSION,
                            realm,
                            read_subs[realm],
                            self.processed_submissions,
                            self.redis,
                        ))

            read_entities = get_prepared(self.extracted_entities, utils.Artifact.ENTITY, self.redis)
            if read_entities:
                for realm in read_entities.keys():
                    self.kernel_comm_pool.apply_async(
                        func=push_to_kernel,
                        args=(
                            utils.Artifact.ENTITY,
                            realm,
                            read_entities[realm],
                            self.extracted_entities,
                            self.redis,
                        ))

            time.sleep(settings.WAIT_INTERVAL)

        _logger.info('Manager caught stop signal')

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
                self.extracted_entities,
                self.processed_submissions,
                self.redis,
            )
        )


def get_prepared(queue: Queue, _type: utils.Artifact, redis=None) -> Dict[str, Dict]:
    res = defaultdict(list)
    excluded = []
    for _ in range(settings.MAX_PUSH_SIZE):
        try:
            realm, msg = queue.get_nowait()
            if _type is utils.Artifact.ENTITY:
                # check to see if the related submission has been sent off.
                sub_id = msg.get('submission')
                _cache_found = utils.cache_has_object(sub_id, realm, utils.Artifact.SUBMISSION, redis)
                if _cache_found is utils.CacheType.NORMAL:
                    _logger.debug(f'Ignoring entity {msg.get("id")};'
                                  f' submission {sub_id} not sent')
                    excluded.append(tuple([realm, msg]))
                    continue

                elif _cache_found is utils.CacheType.QUARANTINE:
                    _logger.debug(f'Sending entity to Quarantine;'
                                  f' associated with bad submission {sub_id}')
                    utils.quarantine([msg], realm, utils.Artifact.ENTITY, redis)
                    continue

            res[realm].append(msg)
        except Empty:
            break

    for item in excluded:
        queue.put(item)  # back to queue
    return res


def entity_extraction(task, entity_queue, submission_queue, redis=None):
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
        for mapping_id in submission[utils.ARTEFACT_NAMES.mappings]:
            mapping = utils.get_from_redis_or_kernel(
                id=mapping_id,
                model_type=utils.ARTEFACT_NAMES.mappings,
                tenant=tenant,
                redis=redis,
            )
            if not mapping:
                raise ValueError(f'Mapping {mapping_id} not found.')

            try:
                # get required artefacts
                schemas = {}
                schema_decorators = mapping['definition']['entities']
                for schemadecorator_id in mapping[utils.ARTEFACT_NAMES.schemadecorators]:
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

            except Exception as e:
                _logger.info(f'Extraction error {e}')
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
            utils.cache_objects(
                objects=submission_entities,
                realm=task.tenant,
                _type=utils.Artifact.ENTITY,
                queue=entity_queue,
                redis=redis,
            )

        # add to processed submission queue (but only the required fields)
        # Let's assume it's going to fail so we don't reextract if kernel
        # can't accept the results.
        processed_submission = {
            'id': task.id,
            SUBMISSION_PAYLOAD_FIELD: payload,
            SUBMISSION_EXTRACTION_FLAG: is_extracted,
        }
        _logger.debug(f'finished task {task.id}')
        return 1

    except Exception as err:
        _logger.info(f'extractor error: {err}')
        # TODO
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
        utils.cache_objects(
            objects=[processed_submission],
            realm=task.tenant,
            _type=utils.Artifact.SUBMISSION,
            queue=submission_queue,
            redis=redis,
        )
        utils.remove_from_redis(
            id=task.id,
            model_type=utils.ARTEFACT_NAMES.submissions,
            tenant=task.tenant,
            redis=redis,
        )


def push_to_kernel(_type: utils.Artifact, realm: str, objs: List[Any], queue: Queue, redis=None):
    if not objs:
        return 0

    if _type is utils.Artifact.SUBMISSION:
        url = 'submissions/bulk_update_extracted.json'
        method = 'patch'
    elif _type is utils.Artifact.ENTITY:
        url = 'entities.json'
        method = 'post'

    try:
        utils.kernel_data_request(url=url, method=method, data=objs, realm=realm)
        for obj in objs:
            utils.remove_from_cache(obj, realm, _type, redis)
        return len(objs)
    except HTTPError as e:
        if e.response.status_code == 400:
            return handle_kernel_errors(objs, realm, _type, queue, redis)
        else:
            _logger.warning(f'Unexpected HTTP Status from Kernel: {e.response.status_code}')
            utils.cache_objects(objs, realm, _type, queue, redis)
            return 0


def handle_kernel_errors(objs: List[Any], realm: str, _type: utils.Artifact, queue: Queue, redis=None):
    _size = len(objs)
    if _size > 1:
        # break down big failures and retry parts
        # reducing by half each time
        _chunks = utils.halve_iterable(objs)
        _logger.debug(f'Trying smaller chunks than {_size}...')
        return sum([push_to_kernel(_type, realm, chunk, queue, redis) for chunk in _chunks])

    # Move bad object from cache to quarantine
    for obj in objs:
        utils.remove_from_cache(obj, realm, _type, redis)
    utils.quarantine(objs, realm, _type, redis)
    return 0
