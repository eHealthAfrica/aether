#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
from setuptools import setup

with open(os.path.join('/code', 'VERSION'), 'r') as version_file:
    version = version_file.read().strip()

setup(
    name='aether_producer',
    author='Shawn Sarwar',
    author_email='shawn.sarwar@ehealthafrica.org',
    decription='Kafka Producer for Aether',
    version=version,
    setup_requires=['pytest'],
    tests_require=['pytest', 'sqlalchemy', 'requests', 'aether_producer'],
    url='https://github.com/eHealthAfrica/aether',
    keywords=['aet', 'aether', 'kafka', 'producer'],
    classifiers=[]
)
