#!/usr/bin/env python

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

from io import open
from setuptools import find_packages, setup


def read(f):
    return open(f, 'r', encoding='utf-8').read()


setup(
    version=read('/var/tmp/VERSION').strip(),
    name='aether.common',
    description='A python library with common aether functionality',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',

    url='https://github.com/eHealthAfrica/aether/',
    author='eHealth Africa',
    author_email='aether@ehealthafrica.org',
    license='Apache2 License',

    python_requires='>=3.6',
    install_requires=[
        'django',
        'django-cors-headers',
        'django-debug-toolbar',
        'django-prometheus',
        'django-uwsgi',
        'djangorestframework',
        'psycopg2-binary',
        'pygments',
        'python-json-logger',
        'requests',
    ],
    extras_require={
        'cas': [
            'django-cas-ng<3.6.0',  # breaking changes
            'django-ums-client',
        ],
        'storage': [
            'django-minio-storage',
            'django-storages[boto3,google]',
        ],
        'server': [
            'sentry-sdk',
            'uwsgi',
        ],
        'test': [
            'coverage',
            'flake8',
            'flake8-quotes',
            'mock',
            'tblib',  # for paralell test runner
        ],
    },

    packages=find_packages(exclude=['*tests*']),
    include_package_data=True,
)
