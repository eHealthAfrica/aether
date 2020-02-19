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

from collections import namedtuple
from enum import Enum
from multiprocessing import Queue
from typing import (
    Any,
    List,
    Mapping,
)

from redis import Redis
from requests.exceptions import HTTPError

from aether.python.redis.task import TaskHelper, Task
from aether.python.utils import request

from extractor import settings

_logger = settings.get_logger('Utils')

Constants = namedtuple(
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


class CacheType(Enum):
    NORMAL = 1
    QUARANTINE = 2
    NONE = 3


class HelperManager(object):
    _redis: Redis = None
    _helper: TaskHelper = None

    def __init__(self, redis=None):
        if redis:
            self.set_redis(redis)

    def clear(self):
        _logger.info('clearing handled redis and task helpers')
        self._stop_helper()
        self._redis = None
        self._helper = None

    def _get_default_redis(self):
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            encoding='utf-8',
            decode_responses=True
        )

    def get_redis(self) -> Redis:
        if not self._redis:
            self.set_redis(self._get_default_redis())
        return self._redis

    def get_helper(self) -> TaskHelper:
        if not self._helper:
            self.set_redis()
        return self._helper

    def set_redis(self, redis=None):
        _logger.debug('setting new redis')
        if not redis:
            redis = self._get_default_redis()
        if self._redis:
            _logger.debug('replacing old redis')
            self._stop_helper()
        self._redis = redis
        self._helper = TaskHelper(settings, self._redis)

    def _stop_helper(self):
        if not self._helper:
            return
        try:
            self._helper.stop()
        except Exception as err:
            _logger.info(f'problem stopping old helper: {err}')


REDIS_HANDLER = HelperManager()

ARTEFACT_NAMES = Constants(
    mappings='mappings',
    mappingsets='mappingsets',
    schemas='schemas',
    schemadecorators='schemadecorators',
    submissions='submissions',
    schema_id='schema',
    schema_definition='schema_definition',
)


_NORMAL_CACHE = 'exm_failed_submissions'
_QUARANTINE_CACHE = 'exm_quarantine_submissions'
_FAILED_CACHES = [
    (CacheType.NORMAL, _NORMAL_CACHE),
    (CacheType.QUARANTINE, _QUARANTINE_CACHE),
]


# _DEFAULT_REDIS = None
# _REDIS_TASK = None


# def get_default_base_redis(redis=None):
#     global _DEFAULT_REDIS
#     if (not redis) and (not _DEFAULT_REDIS):
#         _DEFAULT_REDIS = Redis(
#             host=settings.REDIS_HOST,
#             port=settings.REDIS_PORT,
#             password=settings.REDIS_PASSWORD,
#             db=settings.REDIS_DB,
#             encoding='utf-8',
#             decode_responses=True
#         )
#     else:
#         _logger.debug('Not Creating Redis instance')
#     return redis if redis else _DEFAULT_REDIS


# def get_redis(redis=None):
#     global _REDIS_TASK
#     if (not redis) and (not _REDIS_TASK):  # only want one of these
#         _REDIS_TASK = TaskHelper(settings, get_default_base_redis())
#     elif isinstance(redis, TaskHelper):
#         _REDIS_TASK = redis
#     else:
#         _REDIS_TASK = TaskHelper(settings, redis)
#     return _REDIS_TASK


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
    except HTTPError as e:
        _logger.debug(e.response.status_code)
        raise e
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
            _logger.warning(str(e))
            return None

    redis_instance = REDIS_HANDLER.get_helper()
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
    return REDIS_HANDLER.get_helper().remove(id, model_type, tenant)


def get_redis_keys_by_pattern(pattern, redis=None):
    return REDIS_HANDLER.get_helper().get_keys(pattern)


def get_redis_subscribed_message(key, redis=None):
    try:
        doc = REDIS_HANDLER.get_helper().get_by_key(key)
        key = key if isinstance(key, str) else key.decode()
        _type, tenant, _id = key.split(':')

        return Task(id=_id, tenant=tenant, type=_type, data=doc)
    except Exception:
        return None


def redis_subscribe(callback, pattern, redis=None):
    return REDIS_HANDLER.get_helper().subscribe(callback=callback, pattern=pattern, keep_alive=True)


def redis_unsubscribe(redis=None):
    try:
        REDIS_HANDLER.get_helper().stop()
    except Exception as aer:  # pragma: no cover
        _logger.critical(f'could not unsubscribe! {aer}')


def cache_objects(objects: List[Any], realm, queue: Queue, redis=None):
    _logger.debug(f'Caching {len(objects)} objects for realm {realm}')

    redis_instance = REDIS_HANDLER.get_helper()
    try:
        for obj in objects:
            assert ('id' in obj), obj.keys()
            redis_instance.add(obj, _NORMAL_CACHE, realm)
            queue.put(tuple([realm, obj]))
    except Exception as err:  # pragma: no cover
        _logger.critical(f'Could not save failed objects to REDIS {str(err)}')


def cache_has_object(_id: str, realm: str, redis=None) -> CacheType:
    redis_instance = REDIS_HANDLER.get_helper()
    for _cache_type, _key in _FAILED_CACHES:
        if redis_instance.exists(_id, _key, realm):
            return _cache_type
    return CacheType.NONE


def get_failed_objects(queue: Queue, redis=None) -> dict:
    redis_instance = REDIS_HANDLER.get_helper()

    failed = redis_instance.list(_NORMAL_CACHE)
    failed = [i.split(':') for i in failed]  # split "{tenant}:{_id}"
    for tenant, _id in failed:
        res = redis_instance.get(_id, _NORMAL_CACHE, tenant)
        if res:
            del res['modified']
            queue.put(tuple([tenant, res]))
        else:
            _logger.warning(f'Could not fetch object {tenant}:{_id}')


def remove_from_cache(obj: Mapping[Any, Any], realm: str, redis=None):
    redis_instance = REDIS_HANDLER.get_helper()
    _id = obj['id']
    if redis_instance.exists(_id, _NORMAL_CACHE, realm):
        redis_instance.remove(_id, _NORMAL_CACHE, realm)
        return True
    else:
        return False


def quarantine(objects: List[Any], realm, redis=None):
    _logger.warning(f'Quarantine {len(objects)} objects for realm {realm}')

    redis_instance = REDIS_HANDLER.get_helper()
    try:
        for obj in objects:
            assert ('id' in obj), obj.keys()
            redis_instance.add(obj, _QUARANTINE_CACHE, realm)
    except Exception as err:  # pragma: no cover
        _logger.critical(f'Could not save quarantine objects to REDIS {str(err)}')


def remove_from_quarantine(obj: Mapping[Any, Any], realm: str, redis=None):
    redis_instance = REDIS_HANDLER.get_helper()
    _id = obj['id']
    if redis_instance.exists(_id, _QUARANTINE_CACHE, realm):
        redis_instance.remove(_id, _QUARANTINE_CACHE, realm)
        return True
    else:
        return False


def count_quarantined(redis=None) -> dict:
    redis_instance = REDIS_HANDLER.get_helper()
    return sum(1 for _ in redis_instance.list(_QUARANTINE_CACHE))


def halve_iterable(obj):
    _size = len(obj)
    _chunk_size = int(_size / 2) + (_size % 2)
    for i in range(0, _size, _chunk_size):
        yield obj[i:i + _chunk_size]