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

from django.conf import settings
from aether.python.redis.task import TaskHelper

from .constants import PROJECT_ARTEFACT_CACHE


REDIS_TASK = TaskHelper(settings)


def cache_project_artefacts(project, model_name=None, id=None):
    from .project_artefacts import get_project_artefacts

    _realm = settings.DEFAULT_REALM
    _project_id = str(project.pk)
    _artefacts = None
    try:
        _artefacts = REDIS_TASK.get_by_key(f'_{PROJECT_ARTEFACT_CACHE}:{_realm}:{_project_id}')
    except Exception:
        pass

    if _artefacts and model_name and id:
        _artefacts['data'][model_name].append(id)
    else:
        _linked_artefacts = get_project_artefacts(project, include_submissions=True)
        for i in _linked_artefacts:
            if isinstance(_linked_artefacts[i], set):
                _linked_artefacts[i] = list(_linked_artefacts[i])

        _artefacts = {
            'data': _linked_artefacts,
            'id': _project_id
        }
    REDIS_TASK.add(_artefacts, PROJECT_ARTEFACT_CACHE, _realm)


def get_redis_project_artefacts(project):
    _project_id = str(project.pk)
    _realm = settings.DEFAULT_REALM
    try:
        return REDIS_TASK.get_by_key(f'_{PROJECT_ARTEFACT_CACHE}:{_realm}:{_project_id}')
    except Exception:
        return None


def are_all_items_in_object(obj, items):
    for n in items:
        if items[n] and n in obj and items[n] not in obj[n]:
            return False
    return True


def in_same_project_and_cache(artefacts, project):
    _project_id = str(project.pk)
    _key = f'_{PROJECT_ARTEFACT_CACHE}:{settings.DEFAULT_REALM}:{_project_id}'
    try:
        redis_artefacts = REDIS_TASK.get_by_key(_key)['data']
        return are_all_items_in_object(redis_artefacts, artefacts)
    except Exception:
        cache_project_artefacts(project)
        redis_artefacts = REDIS_TASK.get_by_key(_key)['data']
        return are_all_items_in_object(redis_artefacts, artefacts)
