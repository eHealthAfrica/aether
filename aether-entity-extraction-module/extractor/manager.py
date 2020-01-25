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

import time

from collections import defaultdict
from queue import Empty
import multiprocessing as mp
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
    get_redis,
    get_failed_entities,
    get_from_redis_or_kernel,
    get_redis_keys_by_pattern,
    get_redis_subscribed_message,
    kernel_data_request,
    remove_from_failed_cache,
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
        self.pool = mp.Pool()
        self.manager = mp.Manager()
        self.processed_submissions = self.manager.Queue()
        self.extracted_entities = self.manager.Queue()
        self.redis = redis
        # run the main worker loop in a new thread, no need to MP it.
        Thread(target=self.worker).start()
        logger.debug(f'Manager Ready.')

    def callback(self, result):
        logger.info(result)

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
                logger.info(f'pushing {count}')
                for k in read_subs.keys():
                    self.pool.apply_async(
                        push_submissions_to_kernel,
                        (k, read_subs[k]),
                        callback=cb_s)
            # try to load a queue with failed entities
            failed_entities = get_failed_entities(
                self.manager.Queue(),
                settings.MAX_PUSH_SIZE
            )
            if failed_entities.qsize() > 0:
                logger.info(f'getting failed entities: {failed_entities.qsize()}')
                read_entities = self.get_prepared(failed_entities)
            else:
                read_entities = self.get_prepared(self.extracted_entities)
            if read_entities:
                count = sum([len(v) for v in read_entities.values()])
                logger.info(f'pushing {count}')
                for k in read_entities.keys():
                    self.pool.apply_async(
                        push_entities_to_kernel,
                        (k, read_entities[k]),
                        callback=cb_e)
            time.sleep(1)
        logger.info('Manager caught stop signal')

    def stop(self):
        print('stopping')
        self.stopped = True
        self.pool.close()
        self.pool.join()
        print('stopped')

    def subscribe_to_redis_channel(self, callback: callable, channel: str):
        redis_subscribe(callback=callback, pattern=channel, redis=self.redis)

    def handle_pending_submissions(self, channel='*'):
        for key in get_redis_keys_by_pattern(channel, self.redis):
            # logger.info(f'new pending submission {key}')
            self.add_to_queue(get_redis_subscribed_message(key=key, redis=self.redis))

    def add_to_queue(self, task):
        if not task:
            logger.info('No task to enqueue')
            return
        logger.info(f'Adding task: {task.id}')
        self.pool.apply_async(
            entity_extraction,
            (
                task,
                self.extracted_entities,
                self.processed_submissions),
            callback=cb_ingress)
        # enqueue work


def entity_extraction(task, entity_queue, submission_queue):
    # get artifacts from redis
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
            for e in submission_entities:
                entity_queue.put(
                    tuple([
                        task.tenant,
                        e
                    ]))
        # add to processed submission queue (but only the required fields)
        submission_queue.put(
            tuple([
                task.tenant, {
                    'id': task.id,
                    SUBMISSION_PAYLOAD_FIELD: payload,
                    SUBMISSION_EXTRACTION_FLAG: is_extracted,
                }
            ]))
        logger.info(f'finished task {task.id}')
        return 1
    except Exception as err:
        logger.error(f'extractor ERROR!: {err}')
        return 0


def push_entities_to_kernel(realm, entities):
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
            remove_from_failed_cache(i, realm)
        return len(entities)
    except Exception as e:
        logger.error(str(e))
        # cache failed entities on redis for retries later
        cache_failed_entities(entities, realm)
        return 0


def push_submissions_to_kernel(realm, submissions):
    if not submissions:
        logger.info(f'Submissions queue for realm {realm} was empty')
        return
    else:
        logger.info(f'popped {len(submissions)}')

    try:
        # submission_ids = kernel_data_request(
        #     url='submissions/bulk_update_extracted.json',
        #     method='patch',
        #     data=submissions,
        #     realm=realm,
        # )
        # remove submissions from redis
        # for submission_id in submission_ids:
        #     remove_from_redis(
        #         id=submission_id,
        #         model_type=ARTEFACT_NAMES.submissions,
        #         tenant=realm,
        #         redis=get_redis(),
        #     )
        # return len(submission_ids)
        return len(submissions)
    except Exception as e:
        logger.error(str(e))
        return 0
        # back to the queue ???


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
