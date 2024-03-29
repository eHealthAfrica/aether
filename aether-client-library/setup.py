#!/usr/bin/env python

# Copyright (C) 2023 by eHealth Africa : http://www.eHealthAfrica.org
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
from setuptools import find_namespace_packages, setup


def read(f):
    return open(f, 'r', encoding='utf-8').read()


setup(
    version=read('/var/tmp/VERSION').strip(),
    name='aether.client',
    description='A python library with Aether Client functionality',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',

    url='https://github.com/eHealthAfrica/aether/',
    author='eHealth Africa',
    author_email='aether@ehealthafrica.org',
    license='Apache2 License',

    python_requires='>=3.6',
    install_requires=[
        'bravado',
        'jsonschema[format]<4',
        'requests[security]',
        'requests_oauthlib'
    ],

    packages=find_namespace_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
