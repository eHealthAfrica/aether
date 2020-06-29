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
    Dict,
    List,
    Mapping,
    NamedTuple,
    Union
)

from requests.exceptions import HTTPError

from aether.python.redis.task import TaskHelper
from aether.python.utils import request

from aether.extractor import settings

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


class Task(NamedTuple):
    id: str
    tenant: str
    type: str
    data: Union[Dict, None] = None


ARTEFACT_NAMES = Constants(
    mappings='mappings',
    mappingsets='mappingsets',
    schemas='schemas',
    schemadecorators='schemadecorators',
    submissions='submissions',
    schema_id='schema',
    schema_definition='schema_definition',
)

_REDIS_TASK = TaskHelper(settings, None)

_NORMAL_CACHE = 'exm_failed_submissions'
_QUARANTINE_CACHE = 'exm_quarantine_submissions'
_FAILED_CACHES = [
    (CacheType.NORMAL, _NORMAL_CACHE),
    (CacheType.QUARANTINE, _QUARANTINE_CACHE),
]

_logger = settings.get_logger('Utils')


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


def redis_unsubscribe(redis=None):
    try:
        get_redis(redis).stop()
    except Exception:  # pragma: no cover
        pass


def cache_objects(objects: List[Any], realm, queue: Queue, redis=None):
    _logger.debug(f'Caching {len(objects)} objects for realm {realm}')

    redis_instance = get_redis(redis)
    try:
        for obj in objects:
            assert ('id' in obj), obj.keys()
            redis_instance.add(obj, _NORMAL_CACHE, realm)
            queue.put(tuple([realm, obj]))
    except Exception as err:  # pragma: no cover
        _logger.critical(f'Could not save failed objects to REDIS {str(err)}')


def cache_has_object(_id: str, realm: str, redis=None) -> CacheType:
    redis_instance = get_redis(redis)
    for _cache_type, _key in _FAILED_CACHES:
        if redis_instance.exists(_id, _key, realm):
            return _cache_type
    return CacheType.NONE


def get_failed_objects(queue: Queue, redis=None) -> dict:
    redis_instance = get_redis(redis)

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
    redis_instance = get_redis(redis)
    _id = obj['id']
    if redis_instance.exists(_id, _NORMAL_CACHE, realm):
        redis_instance.remove(_id, _NORMAL_CACHE, realm)
        return True
    else:
        return False


def quarantine(objects: List[Any], realm, redis=None):
    _logger.warning(f'Quarantine {len(objects)} objects for realm {realm}')

    redis_instance = get_redis(redis)
    try:
        for obj in objects:
            assert ('id' in obj), obj.keys()
            redis_instance.add(obj, _QUARANTINE_CACHE, realm)
    except Exception as err:  # pragma: no cover
        _logger.critical(f'Could not save quarantine objects to REDIS {str(err)}')


def remove_from_quarantine(obj: Mapping[Any, Any], realm: str, redis=None):
    redis_instance = get_redis(redis)
    _id = obj['id']
    if redis_instance.exists(_id, _QUARANTINE_CACHE, realm):
        redis_instance.remove(_id, _QUARANTINE_CACHE, realm)
        return True
    else:
        return False


def count_quarantined(redis=None) -> dict:
    redis_instance = get_redis(redis)
    return sum(1 for _ in redis_instance.list(_QUARANTINE_CACHE))


def halve_iterable(obj):
    _size = len(obj)
    _chunk_size = int(_size / 2) + (_size % 2)
    for i in range(0, _size, _chunk_size):
        yield obj[i:i + _chunk_size]
