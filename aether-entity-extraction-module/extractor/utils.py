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
import traceback

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
            self.set_redis(self._redis)
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


_NORMAL_CACHE = 'exm_failed'
_QUARANTINE_CACHE = 'exm_quarantine'
_FAILED_CACHES = [
    (CacheType.NORMAL, _NORMAL_CACHE),
    (CacheType.QUARANTINE, _QUARANTINE_CACHE),
]


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


def get_from_redis_or_kernel(id, model_type, tenant=None):
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


def remove_from_redis(id, model_type, tenant):
    return REDIS_HANDLER.get_helper().remove(id, model_type, tenant)


def get_redis_keys_by_pattern(pattern):
    return REDIS_HANDLER.get_helper().get_keys(pattern)


def get_redis_subscribed_message(key):
    try:
        doc = REDIS_HANDLER.get_helper().get_by_key(key)
        key = key if isinstance(key, str) else key.decode()
        _type, tenant, _id = key.split(':')

        return Task(id=_id, tenant=tenant, type=_type, data=doc)
    except Exception:
        return None


def redis_subscribe(callback, pattern):
    return REDIS_HANDLER.get_helper().subscribe(callback=callback, pattern=pattern, keep_alive=True)


def redis_unsubscribe(redis=None):
    try:
        REDIS_HANDLER.get_helper().stop()
    except Exception as aer:  # pragma: no cover
        _logger.critical(f'could not unsubscribe! {aer}')


def cache_objects(objects: List[Any], realm, queue: Queue):
    _logger.debug(f'Caching {len(objects)} objects for realm {realm}')

    redis_instance = REDIS_HANDLER.get_helper()
    try:
        for obj in objects:
            assert ('id' in obj), obj.keys()
            redis_instance.add(obj, _NORMAL_CACHE, realm)
            queue.put(tuple([realm, obj]))
            _logger.warning(f'cached {obj["id"]} for realm {realm}')
    except Exception as err:  # pragma: no cover
        _logger.critical(f'Could not save failed objects to REDIS {str(err)}')
        _logger.info(traceback.format_exc())


def cache_has_object(_id: str, realm: str) -> CacheType:
    redis_instance = REDIS_HANDLER.get_helper()
    for _cache_type, _key in _FAILED_CACHES:
        if redis_instance.exists(_id, _key, realm):
            return _cache_type
    return CacheType.NONE


def count_failed_objects():
    return len(list_failed_objects())


def list_failed_objects():
    redis_instance = REDIS_HANDLER.get_helper()
    failed = redis_instance.list(_NORMAL_CACHE)
    return [tuple(i.split(':')) for i in failed]  # split "{tenant}:{_id}"


def get_failed_objects(queue: Queue) -> dict:
    redis_instance = REDIS_HANDLER.get_helper()
    for tenant, _id in list_failed_objects():
        res = redis_instance.get(_id, _NORMAL_CACHE, tenant)
        del res['modified']
        queue.put(tuple([tenant, res]))


def remove_from_cache(obj: Mapping[Any, Any], realm: str):
    redis_instance = REDIS_HANDLER.get_helper()
    _id = obj['id']
    if redis_instance.exists(_id, _NORMAL_CACHE, realm):
        redis_instance.remove(_id, _NORMAL_CACHE, realm)
        return True
    else:
        return False


def quarantine(objects: List[Any], realm):
    redis_instance = REDIS_HANDLER.get_helper()
    try:
        for obj in objects:
            assert ('id' in obj), obj.keys()
            redis_instance.add(obj, _QUARANTINE_CACHE, realm)
            _logger.warning(f'Quarantined {obj["id"]} for realm {realm}')
            _logger.debug(f'now Quarantined: {list_quarantined()}')
    except Exception as err:  # pragma: no cover
        _logger.critical(f'Could not save quarantine objects to REDIS {str(err)}')


def remove_from_quarantine(obj: Mapping[Any, Any], realm: str):
    redis_instance = REDIS_HANDLER.get_helper()
    _id = obj['id']
    if redis_instance.exists(_id, _QUARANTINE_CACHE, realm):
        redis_instance.remove(_id, _QUARANTINE_CACHE, realm)
        _logger.debug(f'removed {_id} for QUARANTINE')
        return True
    else:
        return False


def list_quarantined():
    redis_instance = REDIS_HANDLER.get_helper()
    failed = redis_instance.list(_QUARANTINE_CACHE)
    return [tuple(i.split(':')) for i in failed]  # split "{tenant}:{_id}"


def count_quarantined() -> int:
    _logger.debug('Asking for quarantine count')
    return len(list_quarantined())


def halve_iterable(obj):
    _size = len(obj)
    _chunk_size = int(_size / 2) + (_size % 2)
    for i in range(0, _size, _chunk_size):
        yield obj[i:i + _chunk_size]
