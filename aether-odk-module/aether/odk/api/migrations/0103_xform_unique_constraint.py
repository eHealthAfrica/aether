# Generated by Django 2.2.7 on 2019-11-21 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('odk', '0102_project_xform_active'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='xform',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='xform',
            constraint=models.UniqueConstraint(fields=('project', 'form_id', 'version'), name='unique_xform_by_project'),
        ),
    ]
