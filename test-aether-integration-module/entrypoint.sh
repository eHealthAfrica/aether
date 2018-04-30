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
# software distributed under the License is distributed on anx
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
set -e


# Define help message
show_help() {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    eval          : eval shell command
    manage        : invoke django manage.py commands

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    setupproddb   : create/migrate database for production
    setuplocaldb  : create/migrate database for development (creates superuser and token)

    test          : run tests
    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output

    start         : start webserver behind nginx
    start_dev     : start webserver for development
    """
}

test_flake8() {
    flake8 /code/. --config=/code/setup.cfg
}

test_coverage() {
    # Python2 Tests !!Must run first as we rely on the schema generation
    python2 setup.py -q test "${@:1}"

    cat /code/conf/extras/good_job.txt

    # Python3 Tests
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

    manage )
        ./manage.py "${@:2}"
    ;;

    pip_freeze )
        rm -rf /tmp/env
        pip2 install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.py2.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.py2.txt
        pip2 freeze --local | grep -v appdir | tee -a conf/pip/requirements.py2.txt

        rm -rf /tmp/env
        pip3 install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.py3.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.py3.txt
        pip3 freeze --local | grep -v appdir | tee -a conf/pip/requirements.py3.txt
    ;;

    setuplocaldb )
        #setup_db
        #setup_initial_data
    ;;

    setupproddb )
        setup_db
    ;;

    test)
        test_flake8
        test_coverage "${@:2}"
    ;;

    test_lint)
        test_flake8
    ;;

    test_coverage)
        test_coverage "${@:2}"
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
