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

from datetime import datetime

from aether.producer.settings import SETTINGS, get_logger


logger = get_logger('producer-kernel')

_WINDOW_SIZE_SEC = int(SETTINGS.get('window_size_sec', 3))
_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


class KernelClient(object):

    def __init__(self):
        # last time kernel was checked for new updates
        self.last_check = None
        self.last_check_error = None
        # limit number of messages in a single batch
        self.limit = int(SETTINGS.get('fetch_size', 100))
        # send when message volume >= batch_size (kafka hard limit is 2MB)
        self.batch_size = int(SETTINGS.get('publish_size', 100_000))

    def get_time_window_filter(self, query_time):
        # You can't always trust that a set from kernel made up of time window
        # start < _time < end is complete if nearly equal(_time, now()).
        # Sometimes rows belonging to that set would show up a couple mS after
        # the window had closed and be dropped. Our solution was to truncate sets
        # based on the insert time and now() to provide a buffer.

        def fn(row):
            committed = datetime.strptime(row.get('modified')[:26], _TIME_FORMAT)
            lag_time = (query_time - committed).total_seconds()
            if lag_time > _WINDOW_SIZE_SEC:
                return True

            elif lag_time < -30.0:
                # Sometimes fractional negatives show up. More than 30 seconds is an issue though.
                logger.warning(f'INVALID LAG INTERVAL: {lag_time}. Check time settings on server.')

            _id = row.get('id')
            logger.debug(f'WINDOW EXCLUDE: ID: {_id}, LAG: {lag_time}')
            return False

        return fn

    def mode(self):
        raise NotImplementedError

    def check_kernel(self):
        raise NotImplementedError

    def get_realms(self):
        raise NotImplementedError

    def get_schemas(self):
        raise NotImplementedError

    def check_updates(self, realm, schema_id, schema_name, modified):
        raise NotImplementedError

    def count_updates(self, realm, schema_id, schema_name, modified=''):
        raise NotImplementedError

    def get_updates(self, realm, schema_id, schema_name, modified):
        raise NotImplementedError
