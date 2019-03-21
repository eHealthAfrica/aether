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

from . import api


def force_put_doc(path, document):
    doc = document.copy()
    r = api.get(path)
    if r.status_code == 404:
        # the doc does not exist
        pass
    else:
        r.raise_for_status()
        j = r.json()
        if '_rev' in j:
            doc['_rev'] = j['_rev']
    r = api.put(path, json=doc)
    r.raise_for_status()
    return r


def fetch_db_docs(dbname, last_seq):
    '''
    get all changed documents in the database since last sequence
    '''
    changes_url = '{}/_changes?style=all_docs&include_docs=true&since={}'.format(dbname, last_seq)

    r = api.get(changes_url)
    r.raise_for_status()
    result = r.json()
    return {
        'last_seq': result['last_seq'],
        'docs': [doc['doc'] for doc in result['results']],
    }
