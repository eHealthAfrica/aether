# Copyright (C) 2020 by eHealth Africa : http://www.eHealthAfrica.org
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

from locust import HttpUser, between

from kernel_taskset import KernelTaskSet
from settings import BASE_HOST


class KernelUser(HttpUser):

    host = BASE_HOST
    tasks = [KernelTaskSet]

    # wating time (in seconds) between two consecutive tasks
    wait_time = between(0.1, 1)
