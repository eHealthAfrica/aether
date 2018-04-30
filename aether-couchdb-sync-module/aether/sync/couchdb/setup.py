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

import json
import os
import os.path

from django.conf import settings
from pathlib import Path

from . import api
from .. import errors
from .utils import force_put_doc
from ..settings import logger


class DuplicateKeyError(ValueError):
    pass


def load_config(directory, strip=False, predicate=None):  # pragma: no cover
    '''
    Load a couchdb configuration from the filesystem, like couchdbkit or couchdb-bootstrap.

    strip: remove leading and trailing whitespace from file contents, like couchdbkit.

    predicate: function that is passed the full path to each file or directory.
        Each entry is only added to the document if predicate returns True.
        Can be used to ignore backup files etc.
    '''
    objects = {}

    if not os.path.isdir(directory):
        raise OSError('No directory: "{0}"'.format(directory))

    for (dirpath, dirnames, filenames) in os.walk(directory, topdown=False):
        key = os.path.split(dirpath)[-1]
        ob = {}  # type: JsonType
        objects[dirpath] = (key, ob)

        for name in filenames:
            fkey = os.path.splitext(name)[0]
            fullname = os.path.join(dirpath, name)
            if predicate and not predicate(fullname):
                continue
            if fkey in ob:
                raise DuplicateKeyError('file "{0}" clobbers key "{1}"'
                                        .format(fullname, fkey))
            with open(fullname, 'r') as f:
                contents = f.read()
                if name.endswith('.json'):
                    contents = json.loads(contents)
                elif strip:
                    contents = contents.strip()
                ob[fkey] = contents

        for name in dirnames:
            if name == '_attachments':
                raise NotImplementedError('_attachments are not supported')
            fullpath = os.path.join(dirpath, name)
            if predicate and not predicate(fullpath):
                continue
            subkey, subthing = objects[fullpath]
            if subkey in ob:
                raise DuplicateKeyError('directory "{0}" clobbers key "{1}"'
                                        .format(fullpath, subkey))
            ob[subkey] = subthing

    return ob


def setup_db(db_name, config, cleanup=False):  # pragma: no cover
    '''
    Setup up a couchdb database from a configuration
    When `cleanup` is True all the data will be wiped from the existing database!
    '''
    ddoc = config.copy()
    # The {db}/_security is its own document in couchdb and we push it seperately.
    # A security document is required.
    if '_security' in config:
        secdoc = ddoc['_security']
        del ddoc['_security']
    else:
        raise errors.CouchDBInitializationError(
            'Provide a security document for the couchdb: ' + db_name
        )

    r = api.get(db_name)
    exists = r.status_code < 400

    # In testing mode we delete existing couchdbs
    if exists and cleanup:
        logger.info('deleting couchdb: ' + db_name)
        r = api.delete(db_name)
        r.raise_for_status()
        exists = False

    if not exists:
        logger.info('creating couchdb: ' + db_name)
        r = api.put(db_name)
        r.raise_for_status()

    if '_id' in ddoc:
        ddoc_url = db_name + '/' + ddoc['_id']
        force_put_doc(ddoc_url, ddoc)

    secdoc_url = db_name + '/_security'
    force_put_doc(secdoc_url, secdoc)


def setup_couchdb(cleanup=False):  # pragma: no cover
    ''' Setup couchdb by loading the configuration from a directory structure '''
    base_path = Path(settings.COUCHDB_DIR)
    dirs = (p for p in base_path.iterdir() if p.is_dir())

    for db_dir in dirs:
        db_name = db_dir.name
        logger.info('setting up couchdb: ' + db_name)
        if settings.TESTING:
            db_name = db_name + '_test'
        config = load_config(str(db_dir))
        setup_db(db_name, config, cleanup=cleanup)
