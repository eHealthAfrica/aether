# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from django.test import RequestFactory, TestCase

from aether.ui.api import models, serializers


class SerializersTests(TestCase):

    def setUp(self):
        super(SerializersTests, self).setUp()
        self.request = RequestFactory().get('/')

    def test__serializers__create_and_update(self):

        project = serializers.ProjectSerializer(
            data={
                'name': 'a project name',
            },
            context={'request': self.request},
        )
        self.assertTrue(project.is_valid(), project.errors)
        project.save()

        # create pipeline
        pipeline = serializers.PipelineSerializer(
            data={
                'name': 'a pipeline name',
                'project': project.data['project_id'],
            },
            context={'request': self.request},
        )
        self.assertTrue(pipeline.is_valid(), pipeline.errors)
        pipeline.save()

        # create pipeline without project
        pipeline = serializers.PipelineSerializer(
            data={
                'name': 'a pipeline without project',
            },
            context={'request': self.request},
        )
        self.assertTrue(pipeline.is_valid(), pipeline.errors)
        pipeline.save()

        self.assertIsNotNone(pipeline.data['project'])
        self.assertEqual(len(pipeline.data['contracts']), 1, 'Created default contract')

        # try to update the pipeline
        pipeline_2 = serializers.PipelineSerializer(
            models.Pipeline.objects.get(pk=pipeline.data['id']),
            data={
                **pipeline.data,
                'input': {},
            },
            context={'request': self.request},
        )
        self.assertTrue(pipeline_2.is_valid(), pipeline_2.errors)
        pipeline_2.save()  # no exceptions raised

        # create contract without pipeline
        contract = serializers.ContractSerializer(
            data={
                'name': 'a contract',
            },
            context={'request': self.request},
        )
        self.assertFalse(contract.is_valid(), contract.errors)

        contract = serializers.ContractSerializer(
            data={
                'name': 'a contract',
                'pipeline': pipeline.data['id'],
                'is_read_only': True,
            },
            context={'request': self.request},
        )
        self.assertTrue(contract.is_valid(), contract.errors)
        contract.save()

        self.assertFalse(contract.data['is_read_only'], 'is_read_only is not editable')

        contract_instance = models.Contract.objects.get(pk=contract.data['id'])

        # update the contract
        contract_2 = serializers.ContractSerializer(
            contract_instance,
            data={
                **contract.data,
                'mapping_rules': [['!#uuid', 'Dest.id']],
            },
            context={'request': self.request},
        )
        self.assertTrue(contract_2.is_valid(), contract_2.errors)
        contract_2.save()  # no exceptions raised

        contract_instance.is_read_only = True
        contract_instance.save()

        # try again to update the contract
        contract_3 = serializers.ContractSerializer(
            contract_instance,
            data={
                **contract_2.data
            },
            context={'request': self.request},
        )
        self.assertTrue(contract_3.is_valid(), contract_3.errors)

        with self.assertRaises(Exception) as ve_c:
            contract_3.save()
        self.assertIn('Contract is read only', str(ve_c.exception))

        # try to update the pipeline
        pipeline_3 = serializers.PipelineSerializer(
            models.Pipeline.objects.get(pk=pipeline.data['id']),
            data={
                **pipeline.data,
                'input': {},
            },
            context={'request': self.request},
        )
        self.assertTrue(pipeline_3.is_valid(), pipeline_3.errors)

        with self.assertRaises(Exception) as ve_p:
            pipeline_3.save()
        self.assertIn('Pipeline is read only', str(ve_p.exception))
