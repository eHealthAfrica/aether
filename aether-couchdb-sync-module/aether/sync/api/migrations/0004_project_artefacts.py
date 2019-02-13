# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-01 06:27
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django_prometheus.models
import uuid


def migrate_current_schemas(apps, schema_editor):
    Project = apps.get_model('sync', 'Project')
    Schema = apps.get_model('sync', 'Schema')

    if Schema.objects.count():
        # create default project and assign to current schemas
        project = Project.objects.create(name='default')
        for schema in Schema.objects.all():
            schema.project = project
            schema.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sync', '0003_schema'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='devicedb',
            options={'ordering': ['-last_synced_date'], 'verbose_name': 'device', 'verbose_name_plural': 'devices'},
        ),
        migrations.AlterModelOptions(
            name='mobileuser',
            options={'ordering': ['email'], 'verbose_name': 'mobile user', 'verbose_name_plural': 'mobile users'},
        ),
        migrations.AlterModelOptions(
            name='schema',
            options={'ordering': ['name'], 'verbose_name': 'schema', 'verbose_name_plural': 'schemas'},
        ),
        migrations.AlterField(
            model_name='devicedb',
            name='device_id',
            field=models.TextField(unique=True, verbose_name='device ID'),
        ),
        migrations.AlterField(
            model_name='devicedb',
            name='last_synced_date',
            field=models.DateTimeField(null=True, verbose_name='Last synced: date'),
        ),
        migrations.AlterField(
            model_name='devicedb',
            name='last_synced_log_message',
            field=models.TextField(null=True, verbose_name='Last synced: log message'),
        ),
        migrations.AlterField(
            model_name='devicedb',
            name='last_synced_seq',
            field=models.TextField(default='0', null=True, verbose_name='Last synced: sequence'),
        ),
        migrations.AlterField(
            model_name='devicedb',
            name='mobileuser',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devices', to='sync.MobileUser', verbose_name='mobile user'),
        ),
        migrations.AlterField(
            model_name='mobileuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='e-mail'),
        ),
        migrations.AlterField(
            model_name='schema',
            name='kernel_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='This ID corresponds to an Aether Kernel Artefact ID.', verbose_name='Kernel ID'),
        ),
        migrations.AlterField(
            model_name='schema',
            name='name',
            field=models.TextField(blank=True, unique=True, verbose_name='name'),
        ),

        migrations.AddField(
            model_name='schema',
            name='avro_schema',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict, blank=True, verbose_name='AVRO schema'),
        ),

        migrations.CreateModel(
            name='Project',
            fields=[
                ('project_id', models.UUIDField(default=uuid.uuid4, help_text='This ID corresponds to an Aether Kernel project ID.', primary_key=True, serialize=False, verbose_name='project ID')),
                ('name', models.TextField(blank=True, default='', null=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'project',
                'verbose_name_plural': 'projects',
                'ordering': ['name'],
                'default_related_name': 'projects',
            },
        ),
        migrations.AddField(
            model_name='schema',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='schemas', to='sync.Project', verbose_name='project'),
        ),
        migrations.RunPython(migrate_current_schemas, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='schema',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schemas', to='sync.Project', verbose_name='project'),
        ),
    ]
