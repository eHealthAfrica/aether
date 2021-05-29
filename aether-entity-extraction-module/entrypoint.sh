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
set -Eeo pipefail

function show_help {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash              : run bash
    eval              : eval shell command

    pip_freeze        : freeze pip dependencies and write to requirements.txt

    start             : start extractor with settings from extractor

    test              : run unit and integration tests.
    test_lint         : run flake8 tests
    """
}

function pip_freeze {
    local VENV=/tmp/env
    rm -rf ${VENV}
    mkdir -p ${VENV}
    python3 -m venv ${VENV}

    ${VENV}/bin/pip install -q \
        -r ./conf/pip/primary-requirements.txt \
        --upgrade

    cat conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
    ${VENV}/bin/pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
}

function test_flake8 {
    flake8
}

function clean_py {
    rm -rf .pytest_cache
    rm -rf aether/extractor/tests/__pycache__
    rm -rf /code/.coverage*
}

function test_py {
    clean_py

    coverage run -m pytest "${@:1}"

    coverage combine --append
    coverage report

    coverage erase
    clean_py

    cat /code/conf/extras/good_job.txt
}

case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    pip_freeze )
        pip_freeze
    ;;

    start )
        ./manage.py
    ;;

    test_lint )
        test_flake8
    ;;

    test )
        test_flake8
        if [ -z "$2" ]; then
            test_py
        else
            test_py "$2"
        fi
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
