# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-23 09:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('odk', '0004_xform_avro_schema'),
    ]

    operations = [

        migrations.RenameField(
            model_name='mapping',
            old_name='mapping_id',
            new_name='project_id',
        ),

        migrations.RenameField(
            model_name='xform',
            old_name='mapping',
            new_name='project',
        ),

        migrations.RenameModel(
            old_name='Mapping',
            new_name='Project',
        ),

        migrations.AddField(
            model_name='xform',
            name='kernel_id',
            field=models.UUIDField(null=True, blank=True, default=uuid.uuid4),
        ),

        migrations.AlterField(
            model_name='project',
            name='surveyors',
            field=models.ManyToManyField(blank=True, related_name='projects', to=settings.AUTH_USER_MODEL),
        ),

    ]
