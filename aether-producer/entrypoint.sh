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
    eval          : eval shell command

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    start         : start producer with settings from file at environment path: PRODUCER_SETTINGS_FILE
    test_unit     : run tests
    """
}

test_unit() {
    pytest -m unit
    cat /code/conf/extras/good_job.txt
    rm -R .pytest_cache
    rm -rf tests/__pycache__
}

case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    pip_freeze )
        pip install virtualenv
        rm -rf /tmp/env

        virtualenv -p python3 /tmp/env/
        /tmp/env/bin/pip install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
        /tmp/env/bin/pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
    ;;


    start )
        ./manage.py
    ;;

    test_unit )
        test_unit
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
