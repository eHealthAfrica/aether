from datetime import datetime
from django.apps import AppConfig
from django_rq import get_scheduler


class ImporterConfig(AppConfig):
    name = 'importer'
    verbose_name = 'Gather2 Sync Importer'

    def ready(self):
        # schedule jobs
        scheduler = get_scheduler('default')

        # Delete any existing job to prevent duplicating them
        for job in scheduler.get_jobs():
            job.delete()

        # run the sync import task every hour since now
        scheduler.schedule(
            scheduled_time=datetime.utcnow(),
            func='importer.tasks.import_synced_devices_task',
            interval=15 * 60,
        )
