# Generated by Django 2.2.3 on 2019-07-24 15:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('odk', '0100_initial_squashed'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='xform',
            unique_together={('project', 'form_id', 'version')},
        ),
    ]
