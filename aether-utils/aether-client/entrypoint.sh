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


# Define help message
show_help() {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    build         : build python wheel of library in /dist
    eval          : eval shell command
    travis_cache  : build the pip requirements for the travis cache
    test          : run tests
    test_lint     : run flake8 tests

    """
}

prep_travis() {
    chown -R root:root /.cache/pip
    pip install -q -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt --cache-dir /.cache/pip
    chown -R 2000:50 /.cache/pip
}

test_flake8() {
    flake8 /code/. --config=/code/setup.cfg
}

test(){
    python3 setup.py -q test "${@:1}"
    cat /code/conf/extras/good_job.txt
    rm -R ./*.egg*
    rm -R .pytest_cache
}

case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    test)
        test_flake8
        test
    ;;

    test_lint)
        test_flake8
    ;;

    travis_cache)
        prep_travis
    ;;

    build)
        # remove previous build if needed
        rm -rf dist
        rm -rf build
        rm -rf aether.client.egg-info

        # create the distribution
        python setup.py bdist_wheel --universal

        # remove useless content
        rm -rf build
        rm -rf aether.client.egg-info
        rm -rf .eggs
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
