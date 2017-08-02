import mock

from django.test import TestCase
from ..tasks import import_synced_devices_task


class ImporterTasksTests(TestCase):

    @mock.patch('importer.tasks.import_synced_devices')
    @mock.patch('api.core_utils.test_connection', return_value=False)
    def test__import_synced_devices_task_without_core(self, mock_test, mock_task):
        self.assertEqual(import_synced_devices_task(), {})
        mock_task.assert_not_called()

    @mock.patch('importer.tasks.import_synced_devices')
    @mock.patch('api.core_utils.test_connection', return_value=True)
    def test__import_synced_devices_task_with_core(self, mock_test, mock_task):
        self.assertNotEqual(import_synced_devices_task(), {})
        mock_task.assert_called()
