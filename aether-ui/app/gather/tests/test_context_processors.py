import mock
from django.test import RequestFactory, TestCase

from ..context_processors import gather_context


class ContextProcessorsTests(TestCase):

    def test_gather_context(self):
        request = RequestFactory().get('/')

        self.assertEqual(gather_context(request), {
            'dev_mode': False,
            'app_name': 'Gather',
            'navigation_list': ['surveys', 'surveyors', ],
            'kernel_url': 'http://kernel-test:9001',
            'odk_url': 'http://odk-test:9002'
        })

    @mock.patch('gather.context_processors.settings.AETHER_ODK', False)
    def test_gather_context__mocked(self):
        request = RequestFactory().get('/')
        context = gather_context(request)

        self.assertNotIn('odk_url', context)
        self.assertEqual(context['navigation_list'], ['surveys', ])
