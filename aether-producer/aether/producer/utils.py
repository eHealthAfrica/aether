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


def halve_iterable(obj):
    _size = len(obj)
    _chunk_size = int(_size / 2) + (_size % 2)
    for i in range(0, _size, _chunk_size):
        yield obj[i:i + _chunk_size]


def utf8size(obj) -> int:
    if not isinstance(obj, str):
        try:
            obj = json.dumps(obj)
        except json.JSONDecodeError:
            obj = str(obj)
    return len(obj.encode('utf-8'))


def sanitize_topic(topic):
    return ''.join(
        [i if i.isalnum() or i in ['-', '_', '.'] else '_' for i in topic]
    )
