# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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
from uuid import uuid4

from aet.kafka import KafkaConsumer
from kafka.consumer.fetcher import NoOffsetForPartitionError


def get_consumer(kafka_url, topic=None):
    kwargs = {
        'aether_masking_schema_annotation': 'aetherMaskingLevel',
        'aether_emit_flag_field_path': '$.publish',
        'aether_emit_flag_values': [True, False],
        'aether_masking_schema_levels': [0, 1, 2, 3, 4, 5],
        'aether_masking_schema_emit_level': 0,
        'group.id': str(uuid4()),
        'bootstrap.servers': kafka_url,
        'auto.offset.reset': 'earliest',
    }
    consumer = KafkaConsumer(**kwargs)
    if topic:
        consumer.subscribe([topic])
    return consumer


def read(consumer, start='LATEST', verbose=False, timeout=5, num_messages=200):
    messages = []
    if start not in ['FIRST', 'LATEST']:
        raise ValueError(f'{start} it not a valid argument for "start="')
    if start == 'FIRST':
        consumer.seek_to_beginning()

    blank = 0
    while True:
        try:
            poll_result = consumer.poll_and_deserialize(
                num_messages=num_messages,
                timeout=timeout,
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
    for msg in new_records:
        flattened.append(msg.value)
        if verbose:
            _pprint(msg)
    return flattened


def _pprint(obj):
    print(json.dumps(obj, indent=2))
