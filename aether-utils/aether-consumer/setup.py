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

from setuptools import setup, find_packages

setup(
    name='aet.consumer',
    author='Shawn Sarwar',
    author_email="shawn.sarwar@ehealthafrica.org",
    decription='''A library to consume messages from Kafka with added functionality based on
        Aether's schema metadata''',
    version='0.9.0',
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'mock'],
    url='http://github.com/eHealthAfrica/aether',
    install_requires=[
        "kafka",
        "jsonpath_ng",
        "spavro"
    ],
    packages=find_packages(),
    namespace_packages=['aether'],
    keywords=['aet','aether', 'kafka', 'consumer'],
    classifiers=[]
)
