# Generated by Django 2.2.7 on 2019-12-04 09:17

import aether.kernel.api.models
from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_prometheus.models
import model_utils.fields
import uuid


def migrate__update_attachment_md5sum(apps, schema_editor):
    Attachment = apps.get_model('kernel', 'attachment')
    for a in Attachment.objects.all():
        a.save()  # calculate md5sum


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kernel', '0107_attachment_file_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='md5sum',
            field=models.CharField(blank=True, editable=False, max_length=36, verbose_name='file MD5'),
        ),

        migrations.RunPython(
            code=migrate__update_attachment_md5sum,
            reverse_code=migrations.RunPython.noop,
            # The optional elidable argument determines whether or not the operation
            # will be removed (elided) when squashing migrations.
            elidable=True,
        ),

        migrations.CreateModel(
            name='ExportTask',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(editable=False, verbose_name='name')),
                ('settings', django.contrib.postgres.fields.jsonb.JSONField(default=dict, editable=False, verbose_name='settings')),
                ('status_records', models.CharField(blank=True, editable=False, null=True, max_length=20, verbose_name='status records')),
                ('status_attachments', models.CharField(blank=True, editable=False, null=True, max_length=20, verbose_name='status attachments')),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to=settings.AUTH_USER_MODEL, verbose_name='Requested by')),
                ('project', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='kernel.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'task',
                'verbose_name_plural': 'tasks',
                'ordering': ['project__id', '-modified'],
                'default_related_name': 'tasks',
            },
        ),
        migrations.CreateModel(
            name='ExportTaskFile',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(verbose_name='name')),
                ('file', models.FileField(editable=False, max_length=500, upload_to=aether.kernel.api.models.__task_path__, verbose_name='file')),
                ('md5sum', models.CharField(blank=True, editable=False, max_length=36, verbose_name='file MD5')),
                ('task', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='kernel.ExportTask', verbose_name='task')),
            ],
            options={
                'verbose_name': 'export file',
                'verbose_name_plural': 'export files',
                'ordering': ['task__id', 'name'],
                'default_related_name': 'files',
            },
        ),
        migrations.AddIndex(
            model_name='exporttaskfile',
            index=models.Index(fields=['task', 'name'], name='kernel_expo_task_id_440af6_idx'),
        ),
        migrations.AddIndex(
            model_name='exporttask',
            index=models.Index(fields=['project', '-modified'], name='kernel_expo_project_e19d66_idx'),
        ),
        migrations.AddIndex(
            model_name='exporttask',
            index=models.Index(fields=['-modified'], name='kernel_expo_modifie_9b8dbe_idx'),
        ),
    ]
