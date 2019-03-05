# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-20 08:44
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0002_auto_20180910_1403'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contract',
            options={'default_related_name': 'contracts', 'ordering': ('name',), 'verbose_name': 'contract', 'verbose_name_plural': 'contracts'},
        ),
        migrations.AlterModelOptions(
            name='pipeline',
            options={'default_related_name': 'pipelines', 'ordering': ('name',), 'verbose_name': 'pipeline', 'verbose_name_plural': 'pipelines'},
        ),
        migrations.AlterField(
            model_name='contract',
            name='entity_types',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list, null=True, verbose_name='entity types'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='is active?'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='is_read_only',
            field=models.BooleanField(default=False, editable=False, verbose_name='is read only?'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='kernel_refs',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, help_text='These IDs correspond to Aether Kernel artefact IDs.', null=True, verbose_name='Kernel artefact IDs'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='mapping',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list, null=True, verbose_name='mapping rules'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='mapping_errors',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True, verbose_name='mapping errors'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='name',
            field=models.CharField(max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='output',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True, verbose_name='output'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='pipeline',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='ui.Pipeline', verbose_name='pipeline'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='published_on',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='published on'),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='input',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='input JSON'),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='mappingset',
            field=models.UUIDField(blank=True, help_text='This ID corresponds to an Aether Kernel mapping set ID.', null=True, verbose_name='mapping set ID'),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='name',
            field=models.CharField(max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='schema',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='AVRO schema'),
        ),
    ]
