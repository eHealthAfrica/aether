# Generated by Django 2.2.6 on 2019-11-04 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0105_schema_validator'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='active',
            field=models.BooleanField(default=True, verbose_name='active'),
        ),
    ]
