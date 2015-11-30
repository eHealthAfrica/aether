# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='xform',
            name='name',
        ),
        migrations.AddField(
            model_name='xform',
            name='description',
            field=models.TextField(default='', null=True),
        ),
        migrations.AddField(
            model_name='xform',
            name='title',
            field=models.CharField(default='', max_length=64, editable=False),
        ),
    ]
