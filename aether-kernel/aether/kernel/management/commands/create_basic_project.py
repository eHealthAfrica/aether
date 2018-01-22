from django.core.management.base import BaseCommand, CommandError
from aether.kernel.api import models


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        project = models.Project.objects.create(
            revision='1',
            name='demo',
            salad_schema='[]',
            jsonld_context='[]',
            rdf_definition='[]'
        )

        person_schema = models.Schema.objects.create(
            name='Person',
            definition={
                "name": "Person",
                "type": "record",
                "fields": [
                    {
                        "jsonldPredicate": "@id",
                        "type": "string",
                        "name": "id",
                    },
                    {
                        "name": "firstName",
                        "type": [
                            "null",
                            "string"
                        ]
                    },
                    {
                        "name": "familyName",
                        "type": [
                            "null",
                            "string"
                        ]
                    }
                ]
            },
            revision='1'
        )

        projectschema = models.ProjectSchema.objects.create(
            name='Person',
            mandatory_fields='[]',
            transport_rule='[]',
            masked_fields='[]',
            is_encrypted=False,
            project=project,
            schema=person_schema
        )

        mapping = models.Mapping.objects.create(
            name='mapping-1',
            definition={
                "mapping": [
                    [
                        "#!uuid",
                        "Person.id"
                    ],
                    [
                        "firstname",
                        "Person.firstName"
                    ],
                    [
                        "lastname",
                        "Person.familyName"
                    ]
                ],
                "entities": {
                    "Person": str(projectschema.pk)
                }
            },
            revision='1',
            project=project
        )

        print(models.Project.objects.all())
        print(models.Schema.objects.all())
        print(models.ProjectSchema.objects.all())
        print(models.Mapping.objects.all())
