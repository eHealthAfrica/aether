# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-27 09:31
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0018_mappingset_input'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mappingset',
            name='input',
            field=django.contrib.postgres.fields.jsonb.JSONField(),
        ),
    ]
