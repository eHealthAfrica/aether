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

from django.http import JsonResponse

from aether.common.health.utils import test_db_connection


def health(*args, **kwargs):
    '''
    Simple view to check if the system is up.
    '''

    return JsonResponse({})


def check_db(*args, **kwargs):
    '''
    Health check for the default DB connection.
    '''

    db_reachable = test_db_connection()
    if not db_reachable:
        return JsonResponse({}, status=500)

    return JsonResponse({})
