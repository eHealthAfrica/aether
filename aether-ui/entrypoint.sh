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
set -Eeuox pipefail


# Define help message
show_help() {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    eval          : eval shell command
    manage        : invoke django manage.py commands

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    setup_db      : create/migrate database

    test          : run ALL tests
    test_lint     : run flake8, standardjs and sass lint tests
    test_coverage : run python tests with coverage output
    test_py       : alias of test_coverage

    start         : start webserver behind nginx
    start_dev     : start webserver for development
    """
}

pip_freeze() {
    pip install virtualenv
    rm -rf /tmp/env

    virtualenv -p python3 /tmp/env/
    /tmp/env/bin/pip install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.txt --upgrade

    cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
    /tmp/env/bin/pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
}

setup_db() {
    export PGPASSWORD=$RDS_PASSWORD
    export PGHOST=$RDS_HOSTNAME
    export PGUSER=$RDS_USERNAME

    until pg_isready -q; do
        >&2 echo "Waiting for postgres..."
        sleep 1
    done

    if psql -c "" $RDS_DB_NAME; then
        echo "$RDS_DB_NAME database exists!"
    else
        createdb -e $RDS_DB_NAME -e ENCODING=UTF8
        echo "$RDS_DB_NAME database created!"
    fi

    # migrate data model if needed
    ./manage.py migrate --noinput
}

setup_admin() {
    # check if vars exist
    ./conf/check_vars.sh
    # arguments: -u=admin -p=secretsecret -e=admin@ehealthafrica.org -t=01234656789abcdefghij
    ./manage.py setup_admin -p=$ADMIN_PASSWORD
}

test_lint() {
    flake8 ./aether --config=./conf/extras/flake8.cfg
}

test_coverage() {
    export RCFILE=./conf/extras/coverage.rc
    export TESTING=true

    coverage run    --rcfile="$RCFILE" manage.py test "${@:1}"
    coverage report --rcfile="$RCFILE"
    coverage erase

    cat ./conf/extras/good_job.txt
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
        pip_freeze
    ;;

    setup_db )
        setup_db
    ;;

    test)
        test_lint
        test_coverage
    ;;

    test_lint)
        test_lint
    ;;

    test_coverage)
        test_coverage "${@:2}"
    ;;

    test_py)
        test_coverage "${@:2}"
    ;;

    start )
        setup_db
        setup_admin

        # create static assets
        rm -r -f /code/aether/ui/static/*.*
        cp -r /code/aether/ui/assets/bundles/* /code/aether/ui/static
        ./manage.py collectstatic --noinput --clear --verbosity 0
        chmod -R 755 /var/www/static

        # expose version number (if exists)
        cp ./VERSION /var/www/static/VERSION 2>/dev/null || :
        # add git revision (if exists)
        cp ./REVISION /var/www/static/REVISION 2>/dev/null || :

        [ -z "$DEBUG" ] && DISABLE_LOGGING="--disable-logging" || DISABLE_LOGGING=""
        /usr/local/bin/uwsgi --ini /code/conf/uwsgi.ini --http 0.0.0.0:$WEB_SERVER_PORT $DISABLE_LOGGING
    ;;

    start_dev )
        setup_db
        setup_admin

        # cleaning
        rm -r -f /code/aether/ui/static/*.*
        # copy assets bundles folder into static folder
        cp -r /code/aether/ui/assets/bundles/* /code/aether/ui/static

        ./manage.py runserver 0.0.0.0:$WEB_SERVER_PORT
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
