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

function show_help {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    eval          : eval shell command
    manage        : invoke django manage.py commands

    test          : run tests
    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output
    test_py       : alias of test_coverage

    build         : build package library
    """
}

function test_flake8 {
    flake8 /code/. --config=/code/conf/extras/flake8.cfg
}

function test_coverage {
    RCFILE=/code/conf/extras/coverage.rc
    PARALLEL_COV="--concurrency=multiprocessing --parallel-mode"
    PARALLEL_PY="--parallel=4"

    coverage run     --rcfile="$RCFILE" $PARALLEL_COV manage.py test --noinput "${@:1}" $PARALLEL_PY
    coverage combine --rcfile="$RCFILE" --append
    coverage report  --rcfile="$RCFILE"
    coverage erase

    cat /code/conf/extras/good_job.txt
}


case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    manage )
        ./manage.py "${@:2}"
    ;;

    test )
        export TESTING=true
        test_flake8
        test_coverage "${@:2}"
    ;;

    test_lint )
        export TESTING=true
        test_flake8
    ;;

    test_py | test_coverage )
        export TESTING=true
        test_coverage "${@:2}"
    ;;

    build )
        # test before building
        test_flake8
        test_coverage

        # remove previous build if needed
        rm -rf dist/*
        rm -rf build
        rm -rf aether.common.egg-info

        # create the distribution
        python setup.py bdist_wheel --universal

        # remove useless content
        rm -rf build
        rm -rf aether.common.egg-info
    ;;

    help )
        show_help
    ;;

    *)
        show_help
    ;;
esac
