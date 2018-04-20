#!/bin/bash
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
