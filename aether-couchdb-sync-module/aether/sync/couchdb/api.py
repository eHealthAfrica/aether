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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import requests
from django.conf import settings

'''
thin wrapper on top of requests for convenient calls to couchdb
'''

url = settings.COUCHDB_URL
defaults = {'auth': (settings.COUCHDB_USER, settings.COUCHDB_PASSWORD)}


def get(path, *args, **kwargs):
    # ks = {**defaults, **kwargs}
    # http://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.get(url + '/' + path, *args, **ks)


def head(path, *args, **kwargs):
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.get(url + '/' + path, *args, **ks)


def post(path, *args, **kwargs):
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.post(url + '/' + path, *args, **ks)


def put(path, *args, **kwargs):
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.put(url + '/' + path, *args, **ks)


def delete(path, **kwargs):
    ks = defaults.copy()
    ks.update(kwargs)
    return requests.delete(url + '/' + path, **ks)
