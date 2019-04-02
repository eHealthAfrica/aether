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
set -Eeo pipefail

# take uWSGI environment variables from here
if [ ! -z "${CUSTOM_UWSGI_ENV_FILE:-}" ]; then
    touch ${CUSTOM_UWSGI_ENV_FILE}
    source ${CUSTOM_UWSGI_ENV_FILE}
fi

# https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#environment-variables
# When passed as environment variables, options are capitalized and prefixed
# with UWSGI_, and dashes are substituted with underscores.

# Are static assets served by uWSGI?
if [ ! -z "${CUSTOM_UWSGI_SERVE_STATIC:-}" ]; then
    export UWSGI_STATIC_EXPIRES=${UWSGI_STATIC_EXPIRES:-"/* 7776000"}

    ROOT_URL=${STATIC_URL_PREFIX:-/}
    STATIC_DIR="/var/www/static"

    MAP_STATIC="--static-map ${ROOT_URL}static=${STATIC_DIR}"
    MAP_FAVICO="--static-map2 ${ROOT_URL}favicon.ico=${STATIC_DIR}/aether/images/aether.ico"
    STATIC_CONTENT="$MAP_STATIC $MAP_FAVICO"
fi

# set default values
export UWSGI_INI=${UWSGI_INI:-/code/conf/uwsgi/config.ini}

# ensure that DEBUG mode is disabled
export DEBUG=''

/usr/local/bin/uwsgi ${STATIC_CONTENT:-}
