# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-03 10:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0023_auto_20180829_1547'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mappingsetmapping',
            name='mapping',
        ),
        migrations.RemoveField(
            model_name='mappingsetmapping',
            name='mappingset',
        ),
        migrations.AlterField(
            model_name='mapping',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.DeleteModel(
            name='MappingSetMapping',
        ),
    ]
