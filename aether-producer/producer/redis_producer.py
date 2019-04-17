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
from typing import (
    Dict,
    Iterator,
    List,
    Tuple,
    Union
)
from producer.db import (
    Entity,
    Decorator,
    Schema,
    OFFSET_MANAGER
)
from producer.resource import (
    RESOURCE_HELPER,
    ResourceHelper,
    Resource
)


class RedisProducer(object):

    resoure_helper: ResourceHelper
    ignored_decorator_ids: Dict[str, str]

    @classmethod
    def get_entity_key(cls, e: Entity) -> str:
        return f'{e.offset}/{e.decorator_id}/{e.id}'

    @classmethod
    def get_entity_key_parts(cls, key: str) -> List[str]:
        return key.split('/')  # offset, decorator_id, entity_id

    def __init__(self, resoure_helper: ResourceHelper):
        self.resoure_helper = resoure_helper
        self.ignored_decorator_ids = {}

    def ignore_entity_type(self, decorator_id: str) -> None:
        self.ignored_decorator_ids[decorator_id] = datetime.now().isoformat()

    def unignore_entity_type(self, decorator_id: str) -> None:
        del self.ignored_decorator_ids[decorator_id]

    def get_entity_keys(
        self,
        ignored_decorators: Union[List[str], None] = None
    ) -> List[str]:
        # Reading / sorting 100k entities takes on the order of 1.8s
        valid_keys = []
        key_generator = self.resoure_helper.list_ids('entity')
        if ignored_decorators:
            for key in key_generator:
                _, decorator_id, _ = RedisProducer.get_entity_key_parts(key)
                if decorator_id not in ignored_decorators:
                    valid_keys.append(key)
        else:
            valid_keys = list(key_generator)
        valid_keys.sort()
        return valid_keys

    def get_entity_generator(self, entity_keys: List[str]) -> Iterator[Entity]:
        # entity_keys are sorted by offset -> decorator_id -> entity_id
        for key in entity_keys:
            r: Resource = self.resoure_helper.get(key, 'entity')
            yield Entity(**r.data)

    def get_unique_decorator_ids(self, entity_keys: List[str]) -> List[str]:
        unique_keys = set()
        for key in entity_keys:
            _, decorator_id, _ = RedisProducer.get_entity_key_parts(key)
            unique_keys.add(decorator_id)
        return list(unique_keys)

    def get_production_options(
        self,
        decorator_id: str
    ) -> Tuple[str, str, Schema]:  # topic, serialize_mode, schema
        # get decorator by id & cast from Resource -> Decorator
        d: Decorator = Decorator(
            **self.resoure_helper.get(
                decorator_id,
                'decorator').data
        )
        schema: Schema = Schema(
            **self.resoure_helper.get(
                d.schema_id,
                'schema').data
        )
        topic = f'{d.tenant}:{d.topic_name}'
        serialize_mode = d.serialize_mode
        return topic, serialize_mode, schema
