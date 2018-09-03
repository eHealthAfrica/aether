# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-24 13:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0010_auto_20180305_1540'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapping',
            name='revision',
            field=models.TextField(default='1'),
        ),
        migrations.AlterField(
            model_name='project',
            name='jsonld_context',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='rdf_definition',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='revision',
            field=models.TextField(default='1'),
        ),
        migrations.AlterField(
            model_name='project',
            name='salad_schema',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='projectschema',
            name='mandatory_fields',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='projectschema',
            name='masked_fields',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='projectschema',
            name='transport_rule',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='schema',
            name='revision',
            field=models.TextField(default='1'),
        ),
    ]
