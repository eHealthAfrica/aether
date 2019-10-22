#!/usr/bin/env python
#
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
#

import argparse
import os
import sys

from google.cloud import exceptions
from google.cloud import storage

parser = argparse.ArgumentParser()
parser.add_argument('--projects', required=True)
parser.add_argument('--version', required=True)


def get_required(name):
    try:
        return os.environ[name]
    except KeyError as key:
        raise RuntimeError(f'Missing {key} environment variable!')


def setup():
    client = storage.Client()
    client.from_service_account_json(GCS_CREDS)
    bucket = client.get_bucket(GCS_BUCKET)
    if not bucket.exists():
        raise RuntimeError(f'Bucket: {GCS_BUCKET} does not exist or is not accessible.')
    return bucket


def push_release(version, projects):
    bucket = setup()
    for project in projects:
        print(f'Pushing new version "{version}" for project "{project}"...')
        try:
            blob = bucket.blob(f'{project}/version')
            blob.upload_from_string(version, content_type='text/plain')
        except exceptions.GoogleCloudError as err:
            raise RuntimeError(err)


if __name__ == '__main__':
    try:
        GCS_BUCKET = get_required('RELEASE_BUCKET')
        GCS_CREDS = get_required('GOOGLE_APPLICATION_CREDENTIALS')

        args = parser.parse_args()
        projects = args.projects.split(',')
        version = args.version

        push_release(version, projects)
    except Exception as e:
        print(str(e), flush=True)
        sys.exit(1)
