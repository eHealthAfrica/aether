#!/bin/bash
set -Eeuo pipefail


# Define help message
show_help() {
    echo """
    Commands
    ----------------------------------------------------------------------------
    bash          : run bash
    build         : build python wheel of library in /dist
    eval          : eval shell command
    pip_freeze    : freeze pip dependencies and write to requirements.txt
    start         : run application
    test          : run tests
    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output

    """
}

test_flake8() {
    flake8 /code/. --config=/code/conf/extras/flake8.cfg
}

test_coverage() {
    # Python3 Tests
    python3 setup.py test

    cat /code/conf/extras/good_job.txt
    rm -R ./*.egg*
    rm -R .pytest_cache
    rm -rf .eggs
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

        rm -rf /tmp/env
        pip3 install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.txt
        pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.txt
    ;;

    start )
        python ./app/main.py "${@:2}"
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

    build)
        # remove previous build if needed
        rm -rf dist
        rm -rf build
        rm -rf .eggs
        rm -rf myconsumer.egg-info

        # create the distribution
        python setup.py bdist_wheel --universal

        # remove useless content
        rm -rf build
        rm -rf myconsumer.egg-info
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
