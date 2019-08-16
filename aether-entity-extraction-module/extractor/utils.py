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

import json
import collections
from rest_framework import status
from aether.sdk.redis.task import TaskHelper
from aether.sdk.utils import request
from django.conf import settings
from typing import (
    Dict,
    NamedTuple,
    Union,
)

EXTERNAL_APP_KERNEL = 'aether-kernel'
CONSTANTS = collections.namedtuple(
    'CONSTANTS',
    'projects mappingsets mappings schemas single_schema \
    schema_definition schemadecorators submissions'
)

KERNEL_ARTEFACT_NAMES = CONSTANTS(
    projects='projects',
    mappingsets='mappingsets',
    mappings='mappings',
    schemas='schemas',
    single_schema='schema',
    schema_definition='schema_definition',
    schemadecorators='schemadecorators',
    submissions='submissions',
)

MAX_WORKERS = 5

REDIS_INSTANCE = None

REDIS_TASK = TaskHelper(settings, REDIS_INSTANCE)


def get_redis(redis):
    return TaskHelper(settings, redis) if redis else TaskHelper(settings)


class Task(NamedTuple):
    id: str
    tenant: str
    type: str
    data: Union[Dict, None] = None


def kernel_data_request(url='', method='get', data=None, headers=None):
    '''
    Handle request calls to the kernel server
    '''

    res = request(
        method=method,
        url=f'{settings.KERNEL_URL}/{url}',
        json=data or {},
        headers={'Authorization': f'Token {settings.KERNEL_TOKEN}'},
    )

    res.raise_for_status()

    if res.status_code == status.HTTP_204_NO_CONTENT:
        return None
    return json.loads(res.content.decode('utf-8'))


def get_from_redis_or_kernel(id, type, tenant, redis=None):
    '''
    Get resource from redis by key or fetch from kernel and cache in redis.

    Args:

    id: id if the resource to be retrieved,
    type: type of the resource,
    tenant: the current tenant
    '''

    redis = get_redis(redis)

    try:
        # Get from redis
        return redis.get(id, type, tenant)
    except Exception:
        # get from kernel
        url = f'{type}/{id}/'
        try:
            resource = kernel_data_request(url)
            # cache on redis
            redis.add(task=resource, type=type, tenant=tenant)
            return resource
        except Exception:
            return None


def remove_from_redis(id, type, tenant, redis=None):
    redis = get_redis(redis)
    return redis.remove(id, type, tenant)


def get_redis_keys_by_pattern(pattern, redis=None):
    redis = get_redis(redis)
    return redis.get_keys(pattern)


def get_redis_subcribed_message(key, redis=None):
    redis = get_redis(redis)
    doc = redis.get_by_key(key)
    if doc:
        key = key if isinstance(key, str) else key.decode()
        _type, tenant, _id = key.split(':')
        return Task(
            id=_id,
            tenant=tenant,
            type=_type,
            data=doc
        )
    return None


def redis_subscribe(callback, pattern, redis=None):
    redis = get_redis(redis)
    return redis.subscribe(
        callback=callback,
        pattern=pattern,
        keep_alive=True,
    )


def redis_stop(redis):
    redis = get_redis(redis)
    return redis.stop()


def object_contains(test, obj):
    # Recursive object comparison function.
    if obj == test:
        return True
    if isinstance(obj, list):
        return True in [object_contains(test, i) for i in obj]
    elif isinstance(obj, dict):
        return True in [object_contains(test, i) for i in obj.values()]
    return False
