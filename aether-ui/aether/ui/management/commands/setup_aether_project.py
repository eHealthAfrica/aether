import requests

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gather.api.models import Project

AETHER_PROJECT_DATA = {
    'revision': '1',
    'name': 'Gather',
    'salad_schema': '[]',
    'jsonld_context': '[]',
    'rdf_definition': '[]',
}


class Command(BaseCommand):
    help = '''
    Create an Aether Project if it does not already exist.

    This command ensures that there exists an Aether project
    with an id matching the singleton gather.api.models.Project.
    '''

    @property
    def projects_url(self):
        kernel_settings = settings.AETHER_APPS['kernel']
        base_url = kernel_settings['url']
        return '{base_url}/projects/'.format(base_url=base_url)

    @property
    def request_headers(self):
        kernel_settings = settings.AETHER_APPS['kernel']
        token = kernel_settings['token']
        authorization = 'Token {token}'.format(token=token)
        return {'Authorization': authorization}

    def get_aether_project(self, project_id):
        url = '{projects_url}{project_id}'.format(
            projects_url=self.projects_url,
            project_id=project_id,
        )
        return requests.get(
            url=url,
            headers=self.request_headers,
        )

    def get_aether_projects(self):
        return requests.get(
            url=self.projects_url,
            headers=self.request_headers,
        )

    def post_aether_project(self):
        return requests.post(
            url=self.projects_url,
            headers=self.request_headers,
            data=AETHER_PROJECT_DATA,
        )

    def create_aether_project(self):
        msg = 'No existing gather project, creating a new one'
        self.stdout.write(msg)
        response = self.post_aether_project()
        response.raise_for_status()
        json = response.json()
        project_id = json['id']
        project_name = json['name']
        Project.objects.create(
            project_id=project_id,
            project_name=project_name,
        )
        msg = 'Successfully created a Gather project with project id "{}"'
        self.stdout.write(msg.format(project_id))

    def check_matching_aether_project(self, gather_project_id):
        response = Command.get_aether_project(
            self,
            project_id=gather_project_id,
        )
        if response.status_code == 200:
            msg = 'Found matching Aether project with id "{}"'
            project_id = response.json()['id']
            self.stdout.write(msg.format(project_id))
        else:
            msg = (
                'Could not find an existing Aether project matching '
                'gather project id "{}"'
            )
            raise CommandError(msg.format(gather_project_id))

    def handle(self, *args, **options):
        gather_project = Project.objects.first()
        if gather_project:
            self.check_matching_aether_project(gather_project.project_id)
        else:
            self.create_aether_project()
