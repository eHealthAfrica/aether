# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-06 08:37
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20171102_1219'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='id',
            field=models.CharField(default=uuid.uuid4, max_length=50, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='response',
            name='map_revision',
            field=models.TextField(default='1'),
        ),
        migrations.AlterField(
            model_name='response',
            name='revision',
            field=models.TextField(default='1'),
        ),
    ]
