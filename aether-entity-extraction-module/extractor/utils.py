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
import logging
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

_FAILED_ENTITIES_KEY = '_aether_failed_entities'
_REDIS_TASK = TaskHelper(settings, None)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGGING_LEVEL)


class Task(NamedTuple):
    id: str
    tenant: str
    type: str
    data: Union[Dict, None] = None


def get_redis(redis):
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
    res.raise_for_status()
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


def redis_unsubscribe(redis):
    get_redis(redis).stop()


def cache_failed_entities(entities, realm, redis=None):
    redis_instance = get_redis(redis)

    try:
        failed_entities = redis_instance.get_by_key(_FAILED_ENTITIES_KEY)
        failed_entities[realm].append(entities)
    except Exception:
        failed_entities = {realm: entities}

    redis_instance.redis.set(_FAILED_ENTITIES_KEY, json.dumps(failed_entities))


def get_bulk_size(size):
    return settings.MAX_PUSH_SIZE if size > settings.MAX_PUSH_SIZE else size
