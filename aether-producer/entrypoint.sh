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
    bash              : run bash
    eval              : eval shell command

    flake8            : check against code style guidelines
    pip_freeze        : freeze pip dependencies and write to requirements.txt

    start             : start producer with settings from file at environment path: PRODUCER_SETTINGS_FILE

    test              : run unit and integration tests.
    test_lint         : run flake8 tests
    test_integration  : run integration tests
    test_unit         : run unit tests
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

function after_test {
    cat /code/conf/extras/good_job.txt
    rm -rf .pytest_cache
    rm -rf tests/__pycache__
}

function test_unit {
    pytest -m unit
    after_test
}

function test_integration {
    pytest -m integration
    after_test
}

function test_all {
    pytest
    after_test
}

case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    flake8 )
        test_flake8
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

    test_unit )
        test_unit
    ;;

    test_integration )
        test_integration
    ;;

    test )
        test_flake8
        test_all
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
