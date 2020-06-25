#!/usr/bin/env bash
#
# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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
    """
}

function clean_py {
    rm -rf ./*.egg*
    rm -rf .pytest_cache
}

function test_flake8 {
    flake8
}

function test_python {
    clean_py

    export PYTHONDONTWRITEBYTECODE=1
    python3 setup.py -q test "${@:1}"

    cat /code/conf/extras/good_job.txt
    clean_py
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
        test_python "${@:2}"
    ;;

    test_lint )
        test_flake8
    ;;

    help )
        show_help
    ;;

    * )
        show_help
    ;;
esac
