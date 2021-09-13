# Generated by Django 3.1.11 on 2021-05-27 12:57

import aether.sdk.drf.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('odk', '0105_json_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='xform',
            name='avro_schema',
            field=models.JSONField(blank=True, editable=False, null=True, verbose_name='AVRO schema'),
        ),
    ]
