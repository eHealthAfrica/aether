from datetime import datetime
from django.apps import AppConfig
from django_rq import get_scheduler


class Config(AppConfig):
    name = 'aether.sync'
    verbose_name = 'Aether Sync'

    def ready(self):
        # schedule jobs
        scheduler = get_scheduler('default')

        # Delete any existing job to prevent duplicating them
        for job in scheduler.get_jobs():
            job.delete()

        # run the sync import task every hour since now
        scheduler.schedule(
            scheduled_time=datetime.utcnow(),
            func='aether.sync.tasks.import_synced_devices_task',
            interval=15 * 60,
        )
