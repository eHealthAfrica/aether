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
import json
from typing import Dict, NamedTuple, Union

from aether.python.redis.task import TaskHelper
from aether.python.utils import request

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

_FAILED_ENTITIES_KEY = 'exm_failed_entities'
_REDIS_TASK = TaskHelper(settings, None)

logger = settings.get_logger('Utils')


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
    except Exception as err:
        logger.error([err, res.content])
        logger.error(headers)
        c = collections.defaultdict(int)
        if isinstance(data, list):
            for i in data:
                _t = [
                    'schemadecorator',
                    # 'submission',
                    'mapping'
                ]
                print(type(i))
                key = ':::'.join([i.get(t) for t in _t])
                c[key] += 1
            logger.error(data[0])
            logger.error(c)
        else:
            logger.error(data)
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


def get_failed_entities(redis=None) -> dict:
    # TODO don't put all these in one list on Redis
    redis_instance = get_redis(redis)
    failed = redis_instance.list(_FAILED_ENTITIES_KEY)
    failed = [i.split(':') for i in failed]  # split "{tenant}:{_id}"
    cache_result = collections.defaultdict(list)
    for tenant, _id in failed:
        res = redis_instance.get(_id, _FAILED_ENTITIES_KEY, tenant)
        if res:
            cache_result[tenant].append(res)
        else:
            logger.error(f'Could not fetch entity {tenant}:{_id}')
    return cache_result


def cache_failed_entities(entities, realm, redis=None):
    logger.info(f'Caching {len(entities)} failed entities for realm {realm}')
    redis_instance = get_redis(redis)

    try:
        for e in entities:
            assert('id' in e), e.keys()
            redis_instance.add(e, _FAILED_ENTITIES_KEY, realm)
    except Exception as err:
        logger.critical(f'Could not save failed entities to REDIS {err}')


def remove_from_failed_cache(entity, realm, redis=None):
    _id = entity['id']
    redis_instance = get_redis(redis)
    if redis_instance.exists(_id, _FAILED_ENTITIES_KEY, realm):
        redis_instance.remove(_id, _FAILED_ENTITIES_KEY, realm)
        return True
    else:
        return False


def get_bulk_size(size):
    return settings.MAX_PUSH_SIZE if size > settings.MAX_PUSH_SIZE else size
