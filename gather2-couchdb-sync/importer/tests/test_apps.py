from django.apps import apps
from django.test import TestCase
from django_rq import get_scheduler


class AppsTests(TestCase):

    def test_app_config(self):
        self.assertEquals(apps.get_app_config('importer').verbose_name, 'Gather2 Sync Importer')

    def test_scheduler(self):
        scheduler = get_scheduler('default')
        jobs = scheduler.get_jobs()

        self.assertEquals(len(jobs), 1, 'only one job')
