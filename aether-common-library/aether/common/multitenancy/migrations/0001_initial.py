# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-24 12:27
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.MULTITENANCY_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MtInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instance', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mt',
                    to=settings.MULTITENANCY_MODEL,
                    verbose_name='instance',
                    )
                ),
                ('realm', models.TextField(verbose_name='realm')),
            ],
            options={
                'verbose_name': 'instance by realm',
                'verbose_name_plural': 'instances by realm',
                'ordering': ['instance'],
            },
        ),
        migrations.AddIndex(
            model_name='mtinstance',
            index=models.Index(fields=['realm'], name='multitenanc_realm_4d6500_idx'),
        ),
    ]
