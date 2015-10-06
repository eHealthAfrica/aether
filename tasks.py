from invoke import run, task

import os
os.environ['PATH'] += ":{}/bin/".format(
    os.path.dirname(os.path.abspath(__file__))
)

@task
def runserver(configuration="Dev"):
    run("bin/python ./gather2-core/manage.py runserver --configuration {}".format(
      configuration
    ))

@task
def test(configuration="Test"):
    run("cd gather2-core && DJANGO_CONFIGURATION={} py.test core/tests.py".format(
        configuration
    ))

