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

    flake8            : check against code style guidelines
    pip_freeze        : freeze pip dependencies and write to requirements.txt

    start             : start extractor with settings from extractor

    test              : run unit and integration tests.
    test_lint         : run flake8 tests
    """
}

function test_flake8 {
    flake8 /code/. --config=/code/setup.cfg
}

function test {
    rm -R /code/.coverage* 2>/dev/null || true
    coverage run -m pytest "${@:1}"
    coverage report
    coverage erase
    cat /code/conf/extras/good_job.txt
    rm -R .pytest_cache
    rm -rf tests/__pycache__
}

function test_all {
    test
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
        pip install -q virtualenv
        rm -rf /tmp/env

        virtualenv -p python3 /tmp/env/
        /tmp/env/bin/pip install -q -r ./conf/pip/primary-requirements.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
        /tmp/env/bin/pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
    ;;

    start )
        ./manage.py
    ;;

    test_lint )
        test_flake8
    ;;

    test )
        test_flake8
        if [ -z "$2" ]
        then
            test_all
        else
            test "$2"
        fi
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
