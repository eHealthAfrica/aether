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

from google.cloud import exceptions
from google.cloud import storage

parser = argparse.ArgumentParser()
parser.add_argument('--projects', required=True)
parser.add_argument('--version', required=True)


def setup():
    client = storage.Client()
    bucket_name = os.getenv('RELEASE_BUCKET')
    client.from_service_account_json(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    bucket = client.get_bucket(bucket_name)
    if not bucket.exists():
        raise ValueError(f'Bucket: {bucket_name} does not exist or is not accessible.')
    return bucket


def push_release():
    bucket = setup()
    args = parser.parse_args()
    for project in args.projects.split(','):
        try:
            blob = bucket.blob('{}/version'.format(project))
            blob.upload_from_string(args.version, content_type='text/plain')
        except exceptions.GoogleCloudError as err:
            raise ValueError(err)


if __name__ == '__main__':
    push_release()
