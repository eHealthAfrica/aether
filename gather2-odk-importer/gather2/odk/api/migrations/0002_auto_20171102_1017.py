# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-02 10:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('odk', '0001_initial_squashed__0010'),
    ]

    operations = [
        migrations.RenameField(
            model_name='survey',
            old_name='survey_id',
            new_name='mapping_id',
        ),
    ]
