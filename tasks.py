from invoke import run, task

import os

os.environ['PATH'] += ":{}/bin/".format(
    os.path.dirname(os.path.abspath(__file__))
)


def _run(cmd):
    print("+{}".format(cmd))
    run(cmd)


@task
def manage(cmd, configuration="Dev"):
    _run("DJANGO_CONFIGURATION={} bin/python ./gather2_core/manage.py {}".format(
        configuration, cmd,
    ))


@task
def runserver(configuration="Dev"):
    manage("runserver", configuration)


@task
def test(configuration="Test"):
    _run("py.test gather2*/tests.py".format(
        configuration
    ))


@task
def check():
    _run("flake8 --exclude migrations --ignore E501,C901 ./gather2_* *.py")


@task
def fix():
    _run("autopep8 -r --in-place --exclude migrations --max-line-length 120 ./gather2_* *.py")
