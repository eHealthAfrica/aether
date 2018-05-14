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
set -Eeuo pipefail


# Define help message
show_help() {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    eval          : eval shell command
    manage        : invoke manage.py commands

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    start         : start in normal mode
    start_dev     : start for test/dev
    start_test     : start for test/dev
    """
}

test_flake8() {
    '''
    flake8 /code/. --config=/code/conf/extras/flake8.cfg
    '''
}

test_coverage() {
    '''
    export RCFILE=/code/conf/extras/coverage.rc
    export TESTING=true
    export DEBUG=false

    coverage run    --rcfile="$RCFILE" manage.py test "${@:1}"
    coverage report --rcfile="$RCFILE"
    coverage erase
    '''
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

    pip_freeze )
        rm -rf /tmp/env
        pip install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
        pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
    ;;


    start )
        ./manage.py
    ;;

    start_dev )

        ./manage.py test
    ;;

    start_test )

        ./manage.py test
    ;;


    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
