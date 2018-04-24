#!/bin/bash
set -Eeuo pipefail


# Define help message
show_help() {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    eval          : eval shell command

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    test          : run tests
    test_lint     : run flake8 tests
    """
}

test_flake8() {
    flake8 /code/. --config=/code/setup.cfg
}

test_coverage() {
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

    pip_freeze )

        rm -rf /tmp/env
        pip3 install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
        pip3 freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
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

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
