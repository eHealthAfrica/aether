#!/usr/bin/env bash
#
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
#
set -Eeuo pipefail

function show_help {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    eval          : eval shell command

    test          : run tests
    test_lint     : run flake8 tests

    build         : build python wheel of library in /dist
    """
}

function test_flake8 {
    flake8
}

function test_python {
    export PYTHONDONTWRITEBYTECODE=1
    pytest -p no:cacheprovider
    cat /code/conf/extras/good_job.txt
}

case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    test )
        test_flake8
        test_python
    ;;

    test_lint )
        test_flake8
    ;;

    build )
        # remove previous build if needed
        rm -rf dist
        rm -rf build
        rm -rf aether.client.egg-info

        # create the distribution
        python3 -m build --wheel

        # remove useless content
        rm -rf build
        rm -rf aether.client.egg-info
        rm -rf .eggs
    ;;

    help )
        show_help
    ;;

    *)
        show_help
    ;;
esac
