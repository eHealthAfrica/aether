# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-06 10:21
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_prometheus.models
import model_utils.fields
import uuid


def migrate_current_pipelines_to_contracts(apps, schema_editor):
        Pipeline = apps.get_model('ui', 'Pipeline')
        Contract = apps.get_model('ui', 'Contract')

        for pipeline in Pipeline.objects.all():
            Contract.objects.create(
                pk=pipeline.pk,
                name=pipeline.name,
                pipeline=pipeline,
                entity_types=pipeline.entity_types,
                mapping=pipeline.mapping,
                mapping_errors=pipeline.mapping_errors,
                output=pipeline.output,
                kernel_refs=pipeline.kernel_refs,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0001_squashed_from_0001_to_0006'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('entity_types', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('mapping', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=[], null=True)),
                ('mapping_errors', django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True)),
                ('output', django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True)),
                ('kernel_refs', django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True)),
                ('published_on', models.DateTimeField(blank=True, editable=False, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_read_only', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['pipeline__id', '-modified'],
                'default_related_name': 'contracts',
            },
        ),
        migrations.AddField(
            model_name='contract',
            name='pipeline',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='ui.Pipeline'),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='project',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.RunPython(migrate_current_pipelines_to_contracts, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='pipeline',
            name='entity_types',
        ),
        migrations.RemoveField(
            model_name='pipeline',
            name='kernel_refs',
        ),
        migrations.RemoveField(
            model_name='pipeline',
            name='mapping',
        ),
        migrations.RemoveField(
            model_name='pipeline',
            name='mapping_errors',
        ),
        migrations.RemoveField(
            model_name='pipeline',
            name='output',
        ),
        migrations.RemoveField(
            model_name='pipeline',
            name='published_on',
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['pipeline', '-modified'], name='ui_contract_pipelin_65143e_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['-modified'], name='ui_contract_modifie_c5b91f_idx'),
        ),
    ]
