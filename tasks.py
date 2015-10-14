from invoke import run, task

import os

os.environ['PATH'] += ":{}/bin/".format(
    os.path.dirname(os.path.abspath(__file__))
)

os.environ['PYTHONPATH'] = "{}/src/".format(
    os.path.dirname(os.path.abspath(__file__))
)


def _run(cmd):
    print("+{}".format(cmd))
    run(cmd)


@task
def manage(cmd, configuration="Dev"):
    _run("DJANGO_CONFIGURATION={} bin/python ./src/gather2_core/manage.py {}".format(
        configuration, cmd,
    ))


@task
def runserver(configuration="Dev"):
    manage("runserver", configuration)


@task
def test(configuration="Test"):
    _run("DJANGO_CONFIGURATION={} py.test src/gather2_core/tests.py".format(
        configuration
    ))


@task
def check():
    _run("flake8 --exclude migrations --ignore E501,C901 ./src/gather2_core *.py")


@task
def fix():
    _run("autopep8 -r --in-place --exclude migrations --max-line-length 120 ./src/gather2_core *.py")
