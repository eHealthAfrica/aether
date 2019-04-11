#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
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
import json
import redis
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    NamedTuple
)

from producer.logger import LOG
from producer.settings import PRODUCER_CONFIG


class Event(NamedTuple):
    resource_id: str
    resource_type: str
    event_type: str


class Resource(NamedTuple):
    id: str
    type: str
    data: Dict


class ResourceHelper(object):

    def __init__(self, settings):
        self.settings = settings
        self.redis_db = settings.get('REDIS_DB')
        self.redis = redis.Redis(
            host=settings.get('REDIS_HOST'),
            port=settings.get('REDIS_PORT'),
            password=settings.get('REDIS_PASSWORD'),
            db=self.redis_db,
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = None
        self._subscribe_thread = None

    # Generic Redis Resource Functions
    def add(self, resource: Dict[str, Any], type: str) -> bool:
        key = '_{type}:{_id}'.format(
            type=type, _id=resource['id']
        )
        resource['modified'] = datetime.now().isoformat()
        return self.redis.set(key, json.dumps(resource))

    def exists(self, _id: str, type: str) -> bool:
        resource_id = '_{type}:{_id}'.format(
            type=type,
            _id=_id
        )
        if self.redis.exists(resource_id):
            return True
        return False

    def remove(self, _id: str, type: str) -> bool:
        resource_id = '_{type}:{_id}'.format(
            type=type,
            _id=_id
        )
        res = self.redis.delete(resource_id)
        if not res:
            return False
        return True

    def get(self, _id: str, type: str) -> Resource:
        resource_id = f'_{type}:{_id}'
        resource = self.redis.get(resource_id)
        if not resource:
            raise ValueError('No resource with id {resource_id}'.format(resource_id=resource_id))
        return Resource(
            id=_id,
            type=type,
            data=json.loads(resource)
        )

    def list_ids(self, type: str) -> Iterable[str]:
        # ids of matching assets as a generator
        if type:
            key_identifier = '_{type}:*'.format(type=type)
            for i in self.redis.scan_iter(key_identifier):
                yield str(i).split(key_identifier[:-1])[1]
        else:
            key_identifier = '*'
            for i in self.redis.scan_iter(key_identifier):
                yield str(i).split(':')[-1]

    def list(self, type: str) -> Iterable[Resource]:
        # matching assets as a generator
        if type:
            key_identifier = '_{type}:*'.format(type=type)
            for i in self.redis.scan_iter(key_identifier):
                _id = str(i).split(key_identifier[:-1])[1]
                yield(self.get(_id, type))
        else:
            key_identifier = '*'
            for i in self.redis.scan_iter(key_identifier):
                _id = str(i).split(':')[-1]
                yield(self.get(_id, type))

    # subscription resources

    def subscribe(self, callback: Callable, pattern: str):
        if not self._subscribe_thread or not self._subscribe_thread._running:
            self._init_subscriber(callback, pattern)
        else:
            self._subscribe(callback, pattern)

    def _init_subscriber(self, callback: Callable, pattern: str):
        LOG.debug('Initializing Redis subscriber')
        self.pubsub = self.redis.pubsub()
        self._subscribe(callback, pattern)  # Must have a job first of thread dies
        self._subscribe_thread = self.pubsub.run_in_thread(sleep_time=0.1)
        LOG.debug('Subscriber Running')

    def _subscribe(self, callback: Callable, pattern: str):
        LOG.debug(f'Subscribing to {pattern}')
        keyspace = f'__keyspace@{self.redis_db}__:_{pattern}'
        self.pubsub.psubscribe(**{
            f'{keyspace}': self._subscriber_wrapper(callback, keyspace)
        })
        LOG.debug(f'Added {keyspace}')

    def _subscriber_wrapper(
        self,
        fn: Callable,
        registered_channel: str
    ) -> Callable:
        # wraps the callback function so that the message instead of the event will be returned

        def wrapper(msg) -> None:
            LOG.debug(f'callback got message: {msg}')
            channel = msg['channel']
            # get _id from channel: __keyspace@0__:_test:00001 where _id is "_test:00001"
            resource_string = ':'.join(channel.split(':')[1:])
            # split resource into type in name _test:00001 -> _type, 00001
            resource_type, resource_id = resource_string.split(':')
            redis_op = msg['data']
            LOG.debug(f'Channel: {channel} received {redis_op};'
                      + f' registered on: {registered_channel}')
            res = Event(
                resource_id=resource_id,
                resource_type=resource_type,
                event_type=redis_op
            )
            fn(res)  # On callback, hit registered function with proper data
        return wrapper

    def unsubscribe(self, pattern: str) -> None:
        if pattern == '':
            raise AttributeError('A valid pattern must be passed to unsubscribe.')
        LOG.debug(f'Unsubscribing to {pattern}')
        keyspace = f'__keyspace@{self.redis_db}__:_{pattern}'
        self.pubsub.punsubscribe(keyspace)
        LOG.debug(f'Removed {keyspace}')

    def _unsubscribe_all(self) -> None:
        LOG.debug('Unsubscribing from all pub-sub topics')
        self.pubsub.punsubscribe()

    def stop(self, *args, **kwargs) -> None:
        self._unsubscribe_all()
        if self._subscribe_thread and self._subscribe_thread._running:
            LOG.debug('Stopping Subscriber thread.')
            self._subscribe_thread._running = False
            try:
                self._subscribe_thread.stop()
            except (
                redis.exceptions.ConnectionError,
                AttributeError
            ):
                LOG.error('Could not explicitly stop subscribe thread: no connection')


RESOURCE_HELPER = ResourceHelper(PRODUCER_CONFIG)
