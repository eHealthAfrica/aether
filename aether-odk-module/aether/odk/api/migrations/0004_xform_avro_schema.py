# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-18 07:21
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('odk', '0003_media_files'),
    ]

    operations = [
        migrations.AddField(
            model_name='xform',
            name='avro_schema',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True),
        ),
    ]
