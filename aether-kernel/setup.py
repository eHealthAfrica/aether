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

import os
from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='aether.kernel',
    version='0.0.0',
    description='A python module with Aether KERNEL functionality',
    url='https://github.com/eHealthAfrica/aether/',

    author='eHealth Africa',
    author_email='aether@ehealthafrica.org',

    license='Apache2 License',

    packages=find_packages(),
    python_requires='>=2.7, <4',
    install_requires=[
        'django<2',
        'djangorestframework>=3.8<4',
        'djangorestframework-csv>=2.0.0<3',
        'django-cors-headers>=2.0.0<3',
    ],

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',

        'Framework :: Django',
        'Framework :: Django :: 1.11',

        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',

        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python App',
        'Topic :: Software Development :: Libraries :: Django App',
        'Topic :: Software Development :: Libraries :: REST-Framework App',
    ],
)
