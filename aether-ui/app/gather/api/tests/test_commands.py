import os
import requests

from django.core.management.base import CommandError
from django.core.management import call_command
from django.test import TestCase

from gather.api.models import Project
from gather.management.commands.setup_aether_project import Command


def setup_aether_project():
    # Redirect to /dev/null in order to not clutter the test log.
    out = open(os.devnull, 'w')
    call_command('setup_aether_project', stdout=out)


class TestSetupAetherProject(TestCase):

    def delete_aether_project(self, project_id):
        '''
        In order to properly test the management command
        `setup_aether_project`, we need to delete projects in the aether-test
        container.

        This method selectively deletes a single aether project. A more robust
        method would be to delete *all* aether projects in tearDown(), but this
        is obviously more dangerous; if the tests are accidentally run in
        production, we would risk data loss.
        '''
        cmd = Command()
        url = '{projects_url}{project_id}'.format(
            projects_url=cmd.projects_url,
            project_id=project_id,
        )
        response = requests.delete(url=url, headers=cmd.request_headers)
        response.raise_for_status()

    def test__create_aether_project(self):
        setup_aether_project()
        gather_project_id = Project.objects.first().project_id
        self.assertIsNotNone(gather_project_id)
        aether_project_id = Command().get_aether_project(gather_project_id).json()['id']
        self.assertEqual(str(gather_project_id), aether_project_id)
        self.delete_aether_project(aether_project_id)

    def test__check_existing_aether_project(self):
        setup_aether_project()
        gather_project_id_1 = Project.objects.first().project_id
        aether_projects_count_1 = Command().get_aether_projects().json()['count']
        setup_aether_project()
        gather_project_id_2 = Project.objects.first().project_id
        aether_projects_count_2 = Command().get_aether_projects().json()['count']
        self.assertEqual(gather_project_id_1, gather_project_id_2)
        self.assertEqual(aether_projects_count_1, aether_projects_count_2)
        self.delete_aether_project(gather_project_id_1)

    def test__check_existing_aether_project_raises(self):

        def check():
            return Command().check_matching_aether_project('nonexistent')

        self.assertRaises(CommandError, check)
