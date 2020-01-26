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
from enum import Enum
from multiprocessing import Queue
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Union
)

from aether.python.redis.task import TaskHelper
from aether.python.utils import request

from requests.exceptions import HTTPError
from extractor import settings

Constants = collections.namedtuple(
    'Constants',
    (
        'mappings',
        'mappingsets',
        'schemas',
        'schemadecorators',
        'submissions',
        'schema_id',
        'schema_definition',
    )
)

ARTEFACT_NAMES = Constants(
    mappings='mappings',
    mappingsets='mappingsets',
    schemas='schemas',
    schemadecorators='schemadecorators',
    submissions='submissions',
    schema_id='schema',
    schema_definition='schema_definition',
)

SUBMISSION_EXTRACTION_FLAG = 'is_extracted'
SUBMISSION_PAYLOAD_FIELD = 'payload'

_REDIS_TASK = TaskHelper(settings, None)

logger = settings.get_logger('Utils')


class Artifact(Enum):
    ENTITY = 1
    SUBMISSION = 2


NORMAL_CACHE = {
    Artifact.ENTITY: 'exm_failed_entities',
    Artifact.SUBMISSION: 'exm_failed_submissions'
}

QUARENTINE = {
    Artifact.ENTITY: 'exm_quarantine_entities',
    Artifact.SUBMISSION: 'exm_quarantine_submissions'
}


class Task(NamedTuple):
    id: str
    tenant: str
    type: str
    data: Union[Dict, None] = None


def get_redis(redis=None):
    return TaskHelper(settings, redis) if redis else _REDIS_TASK


def kernel_data_request(url='', method='get', data=None, headers=None, realm=None):
    '''
    Handle request calls to the kernel server
    '''

    headers = headers or {}
    headers['Authorization'] = f'Token {settings.KERNEL_TOKEN}'

    _realm = realm if realm else settings.DEFAULT_REALM
    headers[settings.REALM_COOKIE] = _realm

    res = request(
        method=method,
        url=f'{settings.KERNEL_URL}/{url}',
        json=data or {},
        headers=headers,
    )
    try:
        res.raise_for_status()
    except HTTPError as err:
        logger.debug(err.response.status_code)
        raise err
    return res.json()


def get_from_redis_or_kernel(id, model_type, tenant=None, redis=None):
    '''
    Get resource from redis by key or fetch from kernel and cache in redis.

    Args:

    id: id if the resource to be retrieved,
    type: type of the resource,
    tenant: the current tenant
    '''

    def _get_from_kernel():
        try:
            return kernel_data_request(f'{model_type}/{id}.json', realm=tenant)
        except Exception as e:
            logger.error(str(e))
            return None

    redis_instance = get_redis(redis)
    value = None

    try:
        # get from redis or kernel
        value = redis_instance.get(id, model_type, tenant) or _get_from_kernel()
    except Exception:
        # in case of redis error
        value = _get_from_kernel()
    finally:
        try:
            redis_instance.add(task=value, type=model_type, tenant=tenant)
        except Exception:
            pass  # problems with redis or `value` is None
    return value


def remove_from_redis(id, model_type, tenant, redis=None):
    return get_redis(redis).remove(id, model_type, tenant)


def get_redis_keys_by_pattern(pattern, redis=None):
    return get_redis(redis).get_keys(pattern)


def get_redis_subscribed_message(key, redis=None):
    try:
        doc = get_redis(redis).get_by_key(key)
        key = key if isinstance(key, str) else key.decode()
        _type, tenant, _id = key.split(':')

        return Task(id=_id, tenant=tenant, type=_type, data=doc)
    except Exception:
        return None


def redis_subscribe(callback, pattern, redis=None):
    return get_redis(redis).subscribe(callback=callback, pattern=pattern, keep_alive=True)


def get_failed_objects(
    queue: Queue,
    _type: Artifact,
    redis=None
) -> dict:
    _key = NORMAL_CACHE[_type]
    redis_instance = get_redis(redis)
    failed = redis_instance.list(_key)
    failed = [i.split(':') for i in failed]  # split "{tenant}:{_id}"
    for tenant, _id in failed:
        res = redis_instance.get(_id, _key, tenant)
        if res:
            del res['modified']
            queue.put(tuple([
                tenant,
                res
            ]))
        else:
            logger.error(f'Could not fetch {_type} {tenant}:{_id}')


def cache_objects(
    objects: List[Any],
    realm,
    _type: Artifact,
    queue: Queue,
    redis=None
):
    logger.info(f'Caching {len(objects)} object {_type} for realm {realm}')
    _key = NORMAL_CACHE[_type]
    redis_instance = get_redis(redis)

    try:
        for e in objects:
            assert('id' in e), e.keys()
            redis_instance.add(e, _key, realm)
            queue.put(tuple([realm, e]))
    except Exception as err:
        logger.critical(f'Could not save failed objects to REDIS {err}')


def remove_from_cache(
    object: Mapping[Any, Any],
    realm: str,
    _type: Artifact,
    redis=None
):
    _id = object['id']
    _key = NORMAL_CACHE[_type]
    redis_instance = get_redis(redis)
    if redis_instance.exists(_id, _key, realm):
        redis_instance.remove(_id, _key, realm)
        return True
    else:
        return False


quarantine_count = 0


def count_quarantined(
    _type: Artifact,
    redis=None
) -> dict:
    _key = QUARENTINE[_type]
    redis_instance = get_redis(redis)
    return sum(1 for i in redis_instance.list(_key))


def quarantine(
    objects: List[Any],
    realm,
    _type: Artifact,
    redis=None
):
    global quarantine_count
    logger.info(f'Quarantine {len(objects)} object {_type} for realm {realm}')
    _key = QUARENTINE[_type]
    redis_instance = get_redis(redis)
    try:
        for e in objects:
            assert('id' in e), e.keys()
            quarantine_count += 1
            logger.info(f'Quarantine now: {quarantine_count}')
            redis_instance.add(e, _key, realm)
    except Exception as err:
        logger.critical(f'Could not save quarantine objects to REDIS {err}')


def get_bulk_size(size):
    return settings.MAX_PUSH_SIZE if size > settings.MAX_PUSH_SIZE else size
