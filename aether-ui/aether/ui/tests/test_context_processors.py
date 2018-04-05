from django.test import RequestFactory, TestCase

from ..context_processors import ui_context


class ContextProcessorsTests(TestCase):

    def test_ui_context(self):
        request = RequestFactory().get('/')

        self.assertEqual(ui_context(request), {
            'dev_mode': False,
            'app_name': 'Aether UI',
            'kernel_url': 'http://kernel-test:9000',
        })
