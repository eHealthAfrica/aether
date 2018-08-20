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

import os

from io import open
from setuptools import find_packages, setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def read(f):
    return open(f, 'r', encoding='utf-8').read()


setup(
    name='aether.common',
    version='0.0.0',
    description='A python module with common aether functionality',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',

    url='https://github.com/eHealthAfrica/aether/',
    author='eHealth Africa',
    author_email='aether@ehealthafrica.org',
    license='Apache2 License',

    python_requires='>=3.6',
    install_requires=[
        'django<2',
        'django-cors-headers',
        'django-debug-toolbar',
        'django-prometheus',
        'djangorestframework-csv',
        'djangorestframework',
        'psycopg2-binary',
        'requests',
    ],

    packages=find_packages(exclude=['*tests*']),
    include_package_data=True,
)
