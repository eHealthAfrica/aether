import mock
from django.test import RequestFactory, TestCase

from ..context_processors import ui_context


class ContextProcessorsTests(TestCase):

    def test_ui_context(self):
        request = RequestFactory().get('/')

        self.assertEqual(ui_context(request), {
            'dev_mode': False,
            'app_name': 'Ui',
            'navigation_list': ['surveys', 'surveyors', ],
            'kernel_url': 'http://kernel-test:9001',
            'odk_url': 'http://odk-test:9002'
        })

    @mock.patch('ui.context_processors.settings.AETHER_ODK', False)
    def test_ui_context__mocked(self):
        request = RequestFactory().get('/')
        context = ui_context(request)

        self.assertNotIn('odk_url', context)
        self.assertEqual(context['navigation_list'], ['surveys', ])
