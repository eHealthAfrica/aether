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
from time import sleep

from aet.consumer import KafkaConsumer
from kafka.consumer.fetcher import NoOffsetForPartitionError


def get_consumer(kafka_url, topic=None, strategy='latest'):
    consumer = KafkaConsumer(
        aether_emit_flag_required=False,
        group_id='demo-reader',
        bootstrap_servers=[kafka_url],
        auto_offset_reset=strategy,
    )
    if topic:
        consumer.subscribe(topic)
    return consumer


def read(consumer, start='LATEST', verbose=False, timeout_ms=5000, max_records=200):
    messages = []
    if start not in ['FIRST', 'LATEST']:
        raise ValueError(f'{start} it not a valid argument for "start="')
    if start == 'FIRST':
        consumer.seek_to_beginning()

    blank = 0
    while True:
        try:
            poll_result = consumer.poll_and_deserialize(
                timeout_ms=timeout_ms,
                max_records=max_records,
            )
        except NoOffsetForPartitionError as nofpe:
            print(nofpe)
            break

        if not poll_result:
            blank += 1
            if blank > 3:
                break
            sleep(1)

        new_messages = _read_poll_result(poll_result, verbose)
        messages.extend(new_messages)

    print(f'Read {len(messages)} messages')
    return messages


def _read_poll_result(new_records, verbose=False):
    flattened = []
    for packages in new_records.values():
        for package in packages:
            messages = package.get('messages')
            for msg in messages:
                flattened.append(msg)
                if verbose:
                    _pprint(msg)
    return flattened


def _pprint(obj):
    print(json.dumps(obj, indent=2))
