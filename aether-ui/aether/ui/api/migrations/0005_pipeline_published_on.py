# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-24 10:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0004_pipeline_kernel_refs'),
    ]

    operations = [
        migrations.AddField(
            model_name='pipeline',
            name='published_on',
            field=models.DateTimeField(blank=True, null=True, editable=False),
        ),
    ]
