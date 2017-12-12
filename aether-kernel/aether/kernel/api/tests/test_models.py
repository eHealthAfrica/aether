from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
import datetime

from .. import models


class ModelsTests(TransactionTestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'

        self.user = get_user_model().objects.create_user(username, email, password)

    def test_models(self):

        project = models.Project.objects.create(
            revision='rev 1',
            name='a project name',
            salad_schema='a sample salad schema',
            jsonld_context='sample context',
            rdf_definition='a sample rdf definition'
        )
        self.assertEquals(str(project), project.name)
        self.assertNotEqual(models.Project.objects.count(), 0)

        mapping = models.Mapping.objects.create(
            name='sample mapping',
            definition={},
            revision='a sample revision field',
            project=project
        )
        self.assertEquals(str(mapping), mapping.name)
        self.assertNotEqual(models.Mapping.objects.count(), 0)
        self.assertTrue(mapping.definition_prettified is not None)

        submission = models.Submission.objects.create(
            revision='a sample revision',
            map_revision='a sample map revision',
            date=datetime.datetime.now(),
            payload={},
            mapping=mapping
        )
        self.assertEquals(str(submission), '{} - {}'.format(str(mapping), submission.id))
        self.assertNotEqual(models.Submission.objects.count(), 0)
        self.assertTrue(submission.payload_prettified is not None)

        schema = models.Schema.objects.create(
            name='sample schema',
            definition={},
            revision='a sample revision',
            project=project
        )
        self.assertEquals(str(schema), schema.name)
        self.assertNotEqual(models.Schema.objects.count(), 0)
        self.assertTrue(schema.definition_prettified is not None)

        projectschema = models.ProjectSchema.objects.create(
            name='sample project schema',
            mandatory_fields='a sample mandatory fields',
            transport_rule='a sample transport rule',
            masked_fields='a sample masked field',
            is_encrypted=False,
            project=project,
            schema=schema
        )
        self.assertEquals(str(projectschema), projectschema.name)
        self.assertNotEqual(models.ProjectSchema.objects.count(), 0)

        entity = models.Entity.objects.create(
            revision='a sample revision',
            payload={},
            status='a sample status',
            projectschema=projectschema,
            submission=submission
        )
        self.assertEquals(str(entity), 'Entity {}'.format(entity.id))
        self.assertNotEqual(models.Entity.objects.count(), 0)
        self.assertTrue(entity.payload_prettified is not None)
