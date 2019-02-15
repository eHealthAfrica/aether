# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-15 10:49
from __future__ import unicode_literals

import aether.odk.api.models
from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    replaces = [
        ('odk', '0001_initial'),
        ('odk', '0002_rename_survey_to_mapping'),
        ('odk', '0003_media_files'),
        ('odk', '0004_xform_avro_schema'),
        ('odk', '0005_rename_models'),
        ('odk', '0006_verbose_name'),
        ('odk', '0007_xform_modified_at'),
    ]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('project_id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True, default='', null=True)),
                ('surveyors', models.ManyToManyField(blank=True, related_name='mappings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='XForm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(default='', editable=False, verbose_name='xForm title')),
                ('form_id', models.TextField(default='', editable=False, verbose_name='xForm ID')),
                ('xml_data', models.TextField(blank=True, help_text='This XML must conform the ODK XForms specification. http://opendatakit.github.io/xforms-spec/', validators=[aether.odk.api.models.__validate_xml_data__], verbose_name='XML definition')),
                ('description', models.TextField(blank=True, default='', null=True, verbose_name='xForm description')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='xforms', to='odk.Project', verbose_name='project')),
                ('surveyors', models.ManyToManyField(blank=True, help_text='If you do not specify any surveyors, EVERYONE will be able to access this xForm.', related_name='xforms', to=settings.AUTH_USER_MODEL, verbose_name='surveyors')),
                ('md5sum', models.CharField(default='', editable=False, max_length=36, verbose_name='xForm md5sum')),
                ('version', models.TextField(blank=True, default='0', verbose_name='xForm version')),
                ('avro_schema', django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True, verbose_name='AVRO schema')),
                ('kernel_id', models.UUIDField(default=uuid.uuid4, help_text='This ID is used to create Aether Kernel artefacts (schema, project schema and mapping).', verbose_name='Aether Kernel ID')),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='modified at')),
            ],
            options={
                'ordering': ['title', 'form_id', 'version'],
                'verbose_name': 'xform',
                'verbose_name_plural': 'xforms',
            },
        ),
        migrations.CreateModel(
            name='MediaFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, verbose_name='name')),
                ('media_file', models.FileField(upload_to=aether.odk.api.models.__media_path__, verbose_name='file')),
                ('md5sum', models.CharField(editable=False, max_length=36, verbose_name='md5sum')),
                ('xform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media_files', to='odk.XForm', verbose_name='xForm')),
            ],
            options={
                'ordering': ['xform', 'name'],
                'default_related_name': 'media_files',
                'verbose_name': 'media file',
                'verbose_name_plural': 'media files',
            },
        ),
        migrations.AlterField(
            model_name='project',
            name='surveyors',
            field=models.ManyToManyField(blank=True, related_name='projects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterModelOptions(
            name='project',
            options={'ordering': ['name'], 'verbose_name': 'project', 'verbose_name_plural': 'projects'},
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.TextField(blank=True, default='', null=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='project',
            name='project_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='This ID corresponds to an Aether Kernel project ID.', primary_key=True, serialize=False, verbose_name='project ID'),
        ),
        migrations.AlterField(
            model_name='project',
            name='surveyors',
            field=models.ManyToManyField(blank=True, help_text='If you do not specify any surveyors, EVERYONE will be able to access this project xForms.', related_name='projects', to=settings.AUTH_USER_MODEL, verbose_name='surveyors'),
        ),
    ]
