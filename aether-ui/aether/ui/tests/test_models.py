import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import AETHER_APPS, UserTokens, get_or_create_valid_app_token


def mock_return_none(*args):
    return None


def mock_return_false(*args):
    return False


def mock_return_true(*args):
    return True


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class ModelsTests(TestCase):

    def setUp(self):
        username = 'test'
        email = 'test@example.com'
        password = 'testtest'
        self.user = get_user_model().objects.create_user(username, email, password)

    def test__user_tokens__get_app_url(self):
        user_tokens, _ = UserTokens.objects.get_or_create(user=self.user)
        self.assertEqual(user_tokens.get_app_url('kernel'), 'http://kernel-test:9000')
        self.assertEqual(user_tokens.get_app_url('odk-importer'), 'http://odk-importer-test:9443')
        self.assertEqual(user_tokens.get_app_url('other'), None)

    def test__user_tokens__unknown_app(self):
        user_tokens, _ = UserTokens.objects.get_or_create(user=self.user)
        self.assertEqual(user_tokens.kernel_token, None)
        self.assertEqual(user_tokens.odk_importer_token, None)
        self.assertEqual(user_tokens.couchdb_sync_token, None)

        app_name = 'unknown'

        self.assertEqual(user_tokens.get_app_url(app_name), None)
        self.assertEqual(user_tokens.get_app_token(app_name), None)
        self.assertEqual(user_tokens.create_app_token(app_name), None)
        self.assertEqual(user_tokens.get_or_create_app_token(app_name), None)
        self.assertFalse(user_tokens.validates_app_token(app_name))

        with mock.patch('requests.post') as mock_post:
            self.assertEqual(user_tokens.obtain_app_token(app_name), None)
            mock_post.assert_not_called()

        user_tokens.save_app_token(app_name, '9876543210')
        self.assertEqual(user_tokens.kernel_token, None)
        self.assertEqual(user_tokens.odk_importer_token, None)
        self.assertEqual(user_tokens.couchdb_sync_token, None)

    def helper__test_user_tokens__default_values(self, user_tokens, app_name, app_property):
        self.assertNotEqual(user_tokens.get_app_url(app_name), None)
        self.assertEqual(user_tokens.get_app_token(app_name), None)
        self.assertEqual(getattr(user_tokens, app_property), None)
        self.assertFalse(user_tokens.validates_app_token(app_name))

    def helper__test_user_tokens__create_app_token(self, user_tokens, app_name, app_property):
        with mock.patch('requests.post',
                        return_value=MockResponse({'token': 'ABCDEFGH'}, 200)) as mock_post:
            self.assertEqual(user_tokens.create_app_token(app_name), 'ABCDEFGH')
            self.assertEqual(getattr(user_tokens, app_property), 'ABCDEFGH')
            mock_post.assert_called_once()

    def helper__test_user_tokens__get_or_create_app_token(self,
                                                          user_tokens,
                                                          app_name,
                                                          app_property):
        # token DOES exist
        with mock.patch('requests.post') as mock_post:
            self.assertEqual(user_tokens.get_or_create_app_token(app_name), 'ABCDEFGH')
            self.assertEqual(getattr(user_tokens, app_property), 'ABCDEFGH')
            mock_post.assert_not_called()

        # remove token
        user_tokens.save_app_token(app_name, None)
        self.assertEqual(user_tokens.get_app_token(app_name), None)
        self.assertEqual(getattr(user_tokens, app_property), None)

        # token DOES NOT exist
        with mock.patch('requests.post',
                        return_value=MockResponse({'token': '0123456789'}, 200)) as mock_post:
            self.assertEqual(user_tokens.get_or_create_app_token(app_name), '0123456789')
            self.assertEqual(getattr(user_tokens, app_property), '0123456789')
            mock_post.assert_called_once()

    def helper__test_user_tokens__validates_app_token(self, user_tokens, app_name, app_property):
        with mock.patch('requests.get', return_value=mock.Mock(status_code=403)):
            self.assertFalse(user_tokens.validates_app_token(app_name))
        with mock.patch('requests.get', return_value=mock.Mock(status_code=200)):
            self.assertTrue(user_tokens.validates_app_token(app_name))

        # what happens if the base_url for the APP was not set
        with mock.patch('aether.ui.models.UserTokens.get_app_url', new=mock_return_none):
            self.assertFalse(user_tokens.validates_app_token(app_name))

        # None tokens are always not valid
        setattr(user_tokens, app_property, None)
        self.assertFalse(user_tokens.validates_app_token(app_name))

    def helper__test_user_tokens__obtain_app_token(self, user_tokens, app_name, app_property):
        setattr(user_tokens, app_property, '0123456789')

        # obtain token from server, it does not mean that it is saved within the user tokens
        with mock.patch('requests.post',
                        return_value=MockResponse({'token': 'ZYXWVUTSR'}, 200)) as mock_post:
            self.assertEqual(user_tokens.obtain_app_token(app_name), 'ZYXWVUTSR')
            self.assertEqual(user_tokens.get_app_token(app_name), '0123456789')
            self.assertEqual(getattr(user_tokens, app_property), '0123456789')
            mock_post.assert_called_once()

        # what happens if the base_url for the APP was not set
        with mock.patch('aether.ui.models.UserTokens.get_app_url', new=mock_return_none):
            self.assertEqual(user_tokens.obtain_app_token(app_name), None)

        # what happens if the auxiliary token for the APP was not set
        env_var_name = app_name.upper()
        if app_name == 'odk-importer':
            env_var_name = 'ODK'
        with mock.patch('aether.ui.models.AETHER_{}_TOKEN'.format(env_var_name), new=None):
            self.assertEqual(user_tokens.obtain_app_token(app_name), None)

        # with an error on the other side
        with mock.patch('requests.post', return_value=mock.Mock(status_code=403)):
            self.assertEqual(user_tokens.obtain_app_token(app_name), None)

    def test_user_tokens__apps(self):
        for app in AETHER_APPS:
            ut, _ = UserTokens.objects.get_or_create(user=self.user)
            prop = '{}_token'.format(app.replace('-', '_'))

            self.helper__test_user_tokens__default_values(ut, app, prop)
            self.helper__test_user_tokens__create_app_token(ut, app, prop)
            self.helper__test_user_tokens__get_or_create_app_token(ut, app, prop)
            self.helper__test_user_tokens__validates_app_token(ut, app, prop)
            self.helper__test_user_tokens__obtain_app_token(ut, app, prop)

            ut.delete()

    def test_get_or_create_valid_app_token__unknown_app(self):
        self.assertEqual(get_or_create_valid_app_token(self.user, 'other'), None)

    @mock.patch('aether.ui.models.UserTokens.get_app_url', new=mock_return_none)
    def test_get_or_create_valid_app_token__not_base_url(self):
        for app in AETHER_APPS:
            self.assertEqual(get_or_create_valid_app_token(self.user, app), None)

    @mock.patch('aether.ui.models.UserTokens.create_app_token', new=mock_return_none)
    @mock.patch('aether.ui.models.UserTokens.validates_app_token', new=mock_return_false)
    def test_get_or_create_valid_app_token__not_valid_token(self):
        for app in AETHER_APPS:
            self.assertEqual(get_or_create_valid_app_token(self.user, app), None)

    @mock.patch('aether.ui.models.UserTokens.get_app_token', new=mock_return_none)
    @mock.patch('aether.ui.models.UserTokens.validates_app_token', new=mock_return_true)
    def test_get_or_create_valid_app_token__none_token(self):
        for app in AETHER_APPS:
            self.assertEqual(get_or_create_valid_app_token(self.user, app), None)

    @mock.patch('aether.ui.models.UserTokens.validates_app_token', new=mock_return_true)
    def test_get_or_create_valid_app_token__valid_token(self):
        user_tokens, _ = UserTokens.objects.get_or_create(user=self.user)
        for app in AETHER_APPS:
            user_tokens.save_app_token(app, 'ABCDEFGH')
            self.assertEqual(get_or_create_valid_app_token(self.user, app).token,
                             'ABCDEFGH')
