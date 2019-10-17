#!/usr/bin/env python

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
    client.from_service_account_json(os.getenv('GCS_JSON_FILE'))
    bucket = client.get_bucket(bucket_name)
    if not bucket.exists():
        raise ValueError('Bucket: {} does not exist or \
                          is not accessible.'.format(bucket_name))
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
