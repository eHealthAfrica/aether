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

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    setup         : check required environment variables,
                    create/migrate database and,
                    create/update superuser using
                        'ADMIN_USERNAME', 'ADMIN_PASSWORD'

    backup_db     : creates db dump (${BACKUPS_FOLDER}/${DB_NAME}-backup-{timestamp}.sql)
    restore_dump  : restore db dump (${BACKUPS_FOLDER}/${DB_NAME}-backup.sql)

    test          : run tests
    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output
    test_py       : alias of test_coverage

    start         : start webserver behind nginx
    start_dev     : start webserver for development

    health        : checks the system healthy
    check_kernel  : checks communication with kernel
    """
}

function pip_freeze {
    pip install -q virtualenv
    rm -rf /tmp/env

    virtualenv -p python3 /tmp/env/
    /tmp/env/bin/pip install -q -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.txt --upgrade

    cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
    /tmp/env/bin/pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
}

function backup_db {
    pg_isready

    if psql -c "" $DB_NAME; then
        echo "$DB_NAME database exists!"

        pg_dump $DB_NAME > ${BACKUPS_FOLDER}/${DB_NAME}-backup-$(date "+%Y%m%d%H%M%S").sql
        echo "$DB_NAME database backup created."
    fi
}

function restore_db {
    pg_isready

    # backup current data
    backup_db

    # delete DB is exists
    if psql -c "" $DB_NAME; then
        dropdb -e $DB_NAME
        echo "$DB_NAME database deleted."
    fi

    createdb -e $DB_NAME -e ENCODING=UTF8
    echo "$DB_NAME database created."

    # load dump
    psql -e $DB_NAME < ${BACKUPS_FOLDER}/${DB_NAME}-backup.sql
    echo "$DB_NAME database dump restored."

    # migrate data model if needed
    ./manage.py migrate --noinput
}

function setup {
    # check if required environment variables were set
    ./conf/check_vars.sh

    pg_isready

    if psql -c "" $DB_NAME; then
        echo "$DB_NAME database exists!"
    else
        createdb -e $DB_NAME -e ENCODING=UTF8
        echo "$DB_NAME database created!"
    fi

    # migrate data model if needed
    ./manage.py migrate --noinput

    # arguments: -u=admin -p=secretsecret -e=admin@aether.org -t=01234656789abcdefghij
    ./manage.py setup_admin -u=$ADMIN_USERNAME -p=$ADMIN_PASSWORD

    # cleaning
    STATIC_UI=/code/aether/ui/static
    rm -r -f $STATIC_UI && mkdir -p $STATIC_UI
    # copy assets bundles folder into static folder
    cp -r /code/aether/ui/assets/bundles/* $STATIC_UI

    STATIC_ROOT=${STATIC_ROOT:-/var/www/static}
    # create static assets
    ./manage.py collectstatic --noinput --clear --verbosity 0
    chmod -R 755 ${STATIC_ROOT}

    # expose version number (if exists)
    cp /var/tmp/VERSION ${STATIC_ROOT}/VERSION   2>/dev/null || true
    # add git revision (if exists)
    cp /var/tmp/REVISION ${STATIC_ROOT}/REVISION 2>/dev/null || true
}

function test_lint {
    flake8 ./aether --config=./conf/extras/flake8.cfg
}

function test_coverage {
    RCFILE=/code/conf/extras/coverage.rc
    PARALLEL_COV="--concurrency=multiprocessing --parallel-mode"
    PARALLEL_PY="--parallel=${TEST_PARALLEL:-4}"

    rm -R /code/.coverage* 2>/dev/null || true
    coverage run     --rcfile="$RCFILE" $PARALLEL_COV manage.py test --noinput "${@:1}" $PARALLEL_PY
    coverage combine --rcfile="$RCFILE" --append
    coverage report  --rcfile="$RCFILE"
    coverage erase

    cat /code/conf/extras/good_job.txt
}

BACKUPS_FOLDER=/backups

export APP_MODULE=aether.ui
export DJANGO_SETTINGS_MODULE="${APP_MODULE}.settings"

export EXTERNAL_APPS=kernel
export WEBPACK_REQUIRED=true

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
        pip_freeze
    ;;

    setup )
        setup
    ;;

    backup_db )
        backup_db
    ;;

    restore_dump )
        restore_db
    ;;

    test )
        export TESTING=true
        export MULTITENANCY=true

        setup
        test_lint
        test_coverage "${@:2}"
    ;;

    test_lint )
        export TESTING=true
        export MULTITENANCY=true

        test_lint
    ;;

    test_py | test_coverage )
        export TESTING=true
        export MULTITENANCY=true

        test_coverage "${@:2}"
    ;;

    start )
        # ensure that DEBUG mode is disabled
        export DEBUG=

        setup
        ./conf/uwsgi/start.sh
    ;;

    start_dev )
        # ensure that DEBUG mode is enabled
        export DEBUG=true

        setup
        ./manage.py runserver 0.0.0.0:$WEB_SERVER_PORT
    ;;

    health )
        ./manage.py check_url --url=http://0.0.0.0:$WEB_SERVER_PORT/health
    ;;

    check_kernel )
        ./manage.py check_url --url=$EXTERNAL_APP_URL_KERNEL --token=$EXTERNAL_APP_TOKEN_KERNEL
    ;;

    help )
        show_help
    ;;

    * )
        show_help
    ;;
esac
