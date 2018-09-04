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

from django.conf import settings


def resolve_file_url(url):
    '''
    Make all file urls absolute.
    '''
    if url.startswith('/'):
        # For local development, the environment variable DJANGO_STORAGE_BACKEND is
        # set to "filesytem" and files (attachments, media files etc.) are stored on
        # the filesystem and served via nginx. Example URL:
        # http://odk.aether.local/media/<path-to-file>.
        ssl_header = settings.SECURE_PROXY_SSL_HEADER
        scheme = ssl_header[1] if ssl_header else 'http'
        return f'{scheme}://{settings.HOSTNAME}{url}'
    # When the environment variable DJANGO_STORAGE_BACKEND is set to "s3" or
    # "gcs", all file urls will be absolute. Example:
    # https://abcd.s3.amazonaws.com/<file-name>?AWSAccessKeyId=ABC&Signature=ABC%3D&Expires=1534775613.
    return url
