#!/usr/bin/env bash
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
set -Eeuo pipefail

DCA="docker-compose -f ./docker-compose-auth.yml"

$DCA kill
$DCA down
$DCA up -d kongpg keycloakpg db
sleep 3

$DCA build keycloak kernel

$DCA run kong kong migrations bootstrap
$DCA run kong kong migrations up
sleep 3

$DCA up -d kong keycloak

$DCA build auth
$DCA run auth setup_auth
$DCA run auth make_realm
$DCA run kernel manage register_module

$DCA kill auth
$DCA up auth kernel
