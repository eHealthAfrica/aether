# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-04 14:29
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_prometheus.models
import model_utils.fields
import uuid


def migrate_current_mappings_to_mappingsets(apps, schema_editor):
    Mapping = apps.get_model('kernel', 'Mapping')
    MappingSet = apps.get_model('kernel', 'MappingSet')
    Submission = apps.get_model('kernel', 'Submission')

    for mapping in Mapping.objects.all():
        mappingset = MappingSet.objects.create(
            pk=mapping.pk,
            name=mapping.name,
            project=mapping.project,
        )
        mapping.mappingset = mappingset
        mapping.save()

        submissions_by_mapping = Submission.objects.filter(mapping=mapping)
        for submission in submissions_by_mapping:
            submission.mappingset = mappingset
            submission.save()


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0015_auto_20180725_1310'),
    ]

    operations = [
        migrations.CreateModel(
            name='MappingSet',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('revision', models.TextField(default='1')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('input', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
            ],
            options={
                'ordering': ['project__id', '-modified'],
                'default_related_name': 'mappingsets',
            },
        ),
        migrations.RemoveField(
            model_name='submission',
            name='map_revision',
        ),
        migrations.AddField(
            model_name='entity',
            name='mapping',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='entities', to='kernel.Mapping'),
        ),
        migrations.AddField(
            model_name='entity',
            name='mapping_revision',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='mapping',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='mapping',
            name='is_read_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='mapping',
            name='projectschemas',
            field=models.ManyToManyField(related_name='mappings', to='kernel.ProjectSchema'),
        ),
        migrations.AlterField(
            model_name='mapping',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mappings', to='kernel.Project'),
        ),
        migrations.AddField(
            model_name='mappingset',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mappingsets', to='kernel.Project'),
        ),
        migrations.AddField(
            model_name='mapping',
            name='mappingset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mappings', to='kernel.MappingSet'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='submission',
            name='mappingset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='kernel.MappingSet'),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name='mappingset',
            index=models.Index(fields=['project', '-modified'], name='kernel_mapp_project_73242f_idx'),
        ),
        migrations.AddIndex(
            model_name='mappingset',
            index=models.Index(fields=['-modified'], name='kernel_mapp_modifie_46a12a_idx'),
        ),
        migrations.RunPython(migrate_current_mappings_to_mappingsets, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='submission',
            name='mapping',
        ),
    ]
