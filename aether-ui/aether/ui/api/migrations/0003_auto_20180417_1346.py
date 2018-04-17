# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-17 13:46
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0002_remove_usertokens_odk_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityType',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('payload', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'ordering': ('pipeline', 'name'),
                'default_related_name': 'entity_types',
            },
        ),
        migrations.AlterModelOptions(
            name='pipeline',
            options={'ordering': ('name',)},
        ),
        migrations.AddField(
            model_name='pipeline',
            name='input',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='mapping',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='mapping_errors',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='output',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='schema',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AddField(
            model_name='entitytype',
            name='pipeline',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_types', to='ui.Pipeline'),
        ),
        migrations.AlterUniqueTogether(
            name='entitytype',
            unique_together=set([('pipeline', 'name')]),
        ),
    ]
