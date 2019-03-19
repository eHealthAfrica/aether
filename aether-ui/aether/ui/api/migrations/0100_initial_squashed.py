# Generated by Django 2.1.7 on 2019-03-11 12:10

import django.contrib.postgres.fields.jsonb
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid

#
# https://docs.djangoproject.com/en/2.1/topics/migrations/
#
# Once you’ve squashed your migration, you should then commit it alongside
# the migrations it replaces and distribute this change to all running
# instances of your application, making sure that they run migrate
# to store the change in their database.
#
# You must then transition the squashed migration to a normal migration by:
#
# - Deleting all the migration files it replaces.
# - Updating all migrations that depend on the deleted migrations
#   to depend on the squashed migration instead.
# - Removing the replaces attribute in the Migration class of the
#   squashed migration (this is how Django tells that it is a squashed migration).
#

if settings.MULTITENANCY:
    run_before_multitenancy = [
        ('multitenancy', '0001_initial'),
    ]
else:
    run_before_multitenancy = []


class Migration(migrations.Migration):

    initial = True

    run_before = run_before_multitenancy

    dependencies = [
    ]

    replaces = [
        # the squashed migration file cannot be included in the list
        # if it doesn't transition to a normal migration file.
        ('ui', '0001_squashed_from_0001_to_0006'),

        ('ui', '0002_auto_20180910_1403'),
        ('ui', '0003_verbose_name'),
        ('ui', '0004_rename_mapping_to_mapping_rules'),
        ('ui', '0005_project'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('project_id', models.UUIDField(default=uuid.uuid4, help_text='This ID corresponds to an Aether Kernel project ID.', primary_key=True, serialize=False, verbose_name='project ID')),
                ('name', models.TextField(blank=True, default='', null=True, verbose_name='name')),
                ('is_default', models.BooleanField(default=False, editable=False, verbose_name='is the default project?')),
            ],
            options={
                'verbose_name': 'project',
                'verbose_name_plural': 'projects',
                'ordering': ['name'],
                'default_related_name': 'projects',
            },
        ),

        migrations.CreateModel(
            name='Pipeline',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('schema', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='AVRO schema')),
                ('input', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='input JSON')),
                ('mappingset', models.UUIDField(blank=True, help_text='This ID corresponds to an Aether Kernel mapping set ID.', null=True, unique=True, verbose_name='mapping set ID')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pipelines', to='ui.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'pipeline',
                'verbose_name_plural': 'pipelines',
                'ordering': ('name',),
                'default_related_name': 'pipelines',
            },
        ),
        migrations.AddIndex(
            model_name='pipeline',
            index=models.Index(fields=['project', '-modified'], name='ui_pipeline_project_2fab7e_idx'),
        ),
        migrations.AddIndex(
            model_name='pipeline',
            index=models.Index(fields=['-modified'], name='ui_pipeline_modifie_e896fc_idx'),
        ),


        migrations.CreateModel(
            name='Contract',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('entity_types', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list, null=True, verbose_name='entity types')),
                ('mapping_rules', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list, null=True, verbose_name='mapping rules')),
                ('mapping_errors', django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True, verbose_name='mapping errors')),
                ('output', django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, null=True, verbose_name='output')),
                ('mapping', models.UUIDField(blank=True, help_text='This ID corresponds to an Aether Kernel mapping ID.', null=True, unique=True, verbose_name='mapping ID')),
                ('kernel_refs', django.contrib.postgres.fields.jsonb.JSONField(blank=True, editable=False, help_text='These IDs correspond to Aether Kernel artefact IDs.', null=True, verbose_name='Kernel artefact IDs')),
                ('published_on', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='published on')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active?')),
                ('is_read_only', models.BooleanField(default=False, editable=False, verbose_name='is read only?')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='ui.Pipeline', verbose_name='pipeline')),
            ],
            options={
                'verbose_name': 'contract',
                'verbose_name_plural': 'contracts',
                'ordering': ('name',),
                'default_related_name': 'contracts',
            },
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['pipeline', '-modified'], name='ui_contract_pipelin_65143e_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['-modified'], name='ui_contract_modifie_c5b91f_idx'),
        ),
    ]
