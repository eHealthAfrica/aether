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

import os

BASE_HOST = os.environ['BASE_HOST']

AETHER_KERNEL_URL = os.environ['AETHER_KERNEL_URL']
AETHER_KERNEL_TOKEN = os.environ['AETHER_KERNEL_TOKEN']
AETHER_AUTH_HEADER = {'Authorization': f'Token {AETHER_KERNEL_TOKEN}'}

CREATE_PROJECT_PRIORITY = int(os.environ.get('CREATE_PROJECT_PRIORITY', 1))
CREATE_SUBMISSION_PRIORITY = int(os.environ.get('CREATE_SUBMISSION_PRIORITY', 100))
HEALTH_CHECK_PRIORITY = int(os.environ.get('HEALTH_CHECK_PRIORITY', 2))
VIEW_PROJECTS_PRIORITY = int(os.environ.get('VIEW_PROJECTS_PRIORITY', 5))
