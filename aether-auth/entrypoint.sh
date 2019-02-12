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
set -Eeuo pipefail

show_help () {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    eval          : eval shell command

    make_realm    : create realms from the artifacts in /code/realm
    setup_auth    : register keycloak and auth module in Kong.
    register_app  : register aether app in Kong.

    start         : start auth webserver
    """
}

case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    make_realm )
        python /code/src/make_realm.py
    ;;

    setup_auth )
        python /code/src/register_keycloak.py keycloak    ${KEYCLOAK_INTERNAL}
        python /code/src/register_auth.py     ${APP_NAME} ${APP_INTERNAL}
    ;;

    register_app )
        python /code/src/register_app.py "${@:2}"
    ;;

    start )
        python /code/src/app.py
    ;;

    help )
        show_help
    ;;

    * )
        show_help
    ;;
esac
