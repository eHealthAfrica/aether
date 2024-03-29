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
    bash          : run bash
    eval          : eval shell command
    manage        : invoke django manage.py commands

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    setup         : check required environment variables,
                    create/migrate database and,
                    create/update superuser using
                        'ADMIN_USERNAME', 'ADMIN_PASSWORD', 'ADMIN_TOKEN'

    backup_db     : creates db dump (${BACKUPS_FOLDER}/${DB_NAME}-backup-{timestamp}.sql)
    restore_dump  : restore db dump (${BACKUPS_FOLDER}/${DB_NAME}-backup.sql)

    test          : run tests
    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output
    test_py       : alias of test_coverage

    start         : start uWSGI server
    start_dev     : start Django server for development

    health        : checks the system healthy
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

function backup_db {
    pg_isready

    if psql -c "" $DB_NAME; then
        echo "$DB_NAME database exists!"

        mkdir -p $BACKUPS_FOLDER
        local BACKUP_FILE=$BACKUPS_FOLDER/$DB_NAME-backup-$(date "+%Y%m%d%H%M%S").sql

        pg_dump $DB_NAME > $BACKUP_FILE
        chown -f aether:aether $BACKUP_FILE
        echo "$DB_NAME database backup created in [$BACKUP_FILE]."
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

    # clean out expired sessions
    ./manage.py clearsessions

    # arguments: -u=admin -p=secretsecret -e=admin@aether.org -t=01234656789abcdefghij
    ./manage.py setup_admin -u=$ADMIN_USERNAME -p=$ADMIN_PASSWORD -t=$ADMIN_TOKEN

    # create static assets
    echo "Collecting static files..."

    STATIC_ROOT=${STATIC_ROOT:-/var/www/static}
    mkdir -p $STATIC_ROOT

    # cleaning local
    local STATIC_DIR=/code/aether/kernel/static
    rm -r -f $STATIC_DIR && mkdir -p $STATIC_DIR

    # expose version number (if exists)
    cp /var/tmp/VERSION ${STATIC_DIR}/VERSION   2>/dev/null || true
    # add git revision (if exists)
    cp /var/tmp/REVISION ${STATIC_DIR}/REVISION 2>/dev/null || true

    ./manage.py collectstatic --noinput --verbosity 0
    chown -Rf aether:aether ${STATIC_ROOT}
    chmod -R 755 ${STATIC_ROOT}
}

function test_lint {
    flake8
}

function test_coverage {
    coverage erase || true

    coverage run \
        manage.py test \
        --parallel ${TEST_PARALLEL:-} \
        --exclude-tag=nonparallel \
        --noinput \
        "${@:1}"

    # the functions that already use multiprocessing cannot be tested in parallel
    # also the tests linked to attachments
    #   TypeError: Cannot serialize socket object
    coverage run \
        manage.py test \
        --tag=nonparallel \
        --noinput \
        "${@:1}"

    coverage combine --append
    coverage report
    coverage erase

    cat /code/conf/extras/good_job.txt
}

BACKUPS_FOLDER=/backups

export APP_MODULE=aether.kernel
export DJANGO_SETTINGS_MODULE="${APP_MODULE}.settings"

export STORAGE_REQUIRED=true
export REDIS_REQUIRED=true

case "$1" in
    bash )
        bash
    ;;

    eval )
        eval "${@:2}"
    ;;

    manage )
        ./manage.py "${@:2}"
        # required to change migration files owner
        chown -Rf aether:aether *
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
        # Export workaround: in seconds: 20min
        export UWSGI_HARAKIRI=${UWSGI_HARAKIRI:-1200}

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

    help )
        show_help
    ;;

    * )
        show_help
    ;;
esac
