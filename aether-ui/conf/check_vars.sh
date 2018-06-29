#!/bin/bash
#
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
#
set -e

# Production specific functions

check_variable() {
  if [ -n "$1" ];
  then
    echo "$2 set!"
  else
    echo "Missing $2"
    exit -1
  fi
}

check_kernel() {
  # check if KERNEL env variables were set
  check_variable $AETHER_KERNEL_URL   "KERNEL url"
  check_variable $AETHER_KERNEL_TOKEN "KERNEL token"
}

check_kernel
check_variable $ADMIN_PASSWORD "ADMIN password"
