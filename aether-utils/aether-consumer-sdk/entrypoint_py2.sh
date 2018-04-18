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
    manage        : invoke django manage.py commands

    pip_freeze    : freeze pip dependencies and write to requirements.txt

    test          : run tests
    test_lint     : run flake8 tests
    test_coverage : run tests with coverage output

    """
}

test_flake8() {
    flake8 /code/. --config=/code/conf/extras/flake8.cfg
}

test_coverage() {
    # Python2 Tests
    python setup.py -q test

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
        pip install -f ./conf/pip/dependencies -r ./conf/pip/primary-requirements.py2.txt --upgrade

        cat /code/conf/pip/requirements_header.txt | tee conf/pip/requirements.py2.txt
        pip freeze --local | grep -v appdir | tee -a conf/pip/requirements.py2.txt
    ;;

    test)
        # test_flake8
        test_coverage "${@:2}"
    ;;

    test_lint)
        test_flake8
    ;;

    test_coverage)
        test_coverage "${@:2}"
    ;;

    build)
        echo "Please Build from the Python3 Container."
    ;;

    help)
        show_help
    ;;

    *)
        show_help
    ;;
esac
