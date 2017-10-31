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
            definition={},
            revision='a sample revision field',
            project=project
        )
        self.assertEquals(str(mapping), '{} - {}'.format(str(project), mapping.id))
        self.assertNotEqual(models.Mapping.objects.count(), 0)
        self.assertTrue(mapping.definition_prettified is not None)

        response = models.Response.objects.create(
            revision='a sample revision',
            map_revision='a sample map revision',
            date=datetime.datetime.now(),
            payload={},
            mapping=mapping
        )
        self.assertEquals(str(response), '{} - {}'.format(str(mapping), response.id))
        self.assertNotEqual(models.Response.objects.count(), 0)
        self.assertTrue(response.payload_prettified is not None)

        schema = models.Schema.objects.create(
            definition={},
            revision='a sample revision'
        )
        self.assertEquals(str(schema), 'Schema {}'.format(schema.id))
        self.assertNotEqual(models.Schema.objects.count(), 0)
        self.assertTrue(schema.definition_prettified is not None)

        projectschema = models.ProjectSchema.objects.create(
            mandatory_fields='a sample mandatory fields',
            transport_rule='a sample transport rule',
            masked_fields='a sample masked field',
            is_encrypted=False,
            project=project,
            schema=schema
        )
        self.assertEquals(str(projectschema), '{} - {}'.format(str(project), projectschema.id))
        self.assertNotEqual(models.ProjectSchema.objects.count(), 0)

        entity = models.Entity.objects.create(
            revision='a sample revision',
            payload={},
            status='a sample status',
            projectschema=projectschema,
            response=response
        )
        self.assertEquals(str(entity), 'Entity {}'.format(entity.id))
        self.assertNotEqual(models.Entity.objects.count(), 0)
        self.assertTrue(entity.payload_prettified is not None)
