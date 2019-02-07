# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-25 12:16
from __future__ import unicode_literals

from django.db import migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0021_auto_20181023_0711'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created'),
        ),
    ]
