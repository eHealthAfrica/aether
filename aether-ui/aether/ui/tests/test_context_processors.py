import mock
from django.test import RequestFactory, TestCase

from ..context_processors import aether


class ContextProcessorsTests(TestCase):

    def test_aether(self):
        request = RequestFactory().get('/')

        self.assertEqual(aether(request), {
            'dev_mode': False,
            'app_name': 'Aether',
            'org_name': 'eHealth Africa (Dev mode)',
            'odk_active': True,
            'navigation_list': ['surveys', 'surveyors', ],
        })

    @mock.patch('aether.ui.context_processors.settings.AETHER_ODK', False)
    def test_aether__mocked(self):
        request = RequestFactory().get('/')
        context = aether(request)

        self.assertFalse(context['odk_active'])
        self.assertEqual(context['navigation_list'], ['surveys', ])
