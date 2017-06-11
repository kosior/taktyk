import hashlib
import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk import auth
from taktyk import settings


class GetUsernameTest(unittest.TestCase):
    def test_username_exist(self):
        settings.USERNAME = 'UserName'
        self.assertEqual(auth.get_username(), 'UserName')

    @patch('builtins.input')
    def test_username_not_exist(self, test_input):
        settings.USERNAME = ''
        test_input.return_value = 'InputName'
        self.assertEqual(auth.get_username(), 'InputName')


class GetPasswordTest(unittest.TestCase):
    def test_password_exist(self):
        settings.PASSWORD = 'UserPass'
        self.assertEqual(auth.get_password(), 'UserPass')

    @patch('getpass.getpass')
    def test_password_not_exist(self, test_getpass):
        settings.PASSWORD = ''
        test_getpass.return_value = 'InputPass'
        self.assertEqual(auth.get_password(), 'InputPass')


class RestetCredentialsTest(unittest.TestCase):
    def test_if_reset_applied(self):
        settings.USERNAME = 'name'
        settings.PASSWORD = 'pass'
        auth.reset_credentials()
        self.assertIsNone(settings.USERNAME)
        self.assertIsNone(settings.PASSWORD)


class LogInForUserkeyTest(unittest.TestCase):
    def setUp(self):
        settings.USERNAME = 'login123'
        settings.APPKEY = '123appkey'
        self.url = settings.API_LOGIN_URL + '123appkey'

    @patch('requests.post')
    def test_when_api_app_provided_check_if_correct_post_args(self, test_post):
        settings.ACCOUNTKEY = 'acckey123'
        settings.SECRETKEY = 'secret321'
        data = {'login': 'login123', 'accountkey': 'acckey123'}
        headers = auth.apisign(self.url, 'secret321', **data)
        mock_resp = Mock()
        mock_resp.json.return_value = {'userkey': '123'}
        test_post.return_value = mock_resp
        auth.log_in_for_userkey()
        test_post.assert_called_with(self.url, data=data, headers=headers)

    @patch('requests.post')
    def test_when_api_app_provided_check_if_breaks_on_error(self, test_post):
        settings.ACCOUNTKEY = 'acckey123'
        settings.SECRETKEY = 'secret321'
        mock_resp = Mock()
        mock_resp.json.return_value = {}  # this will raise KeyError
        test_post.return_value = mock_resp
        with self.assertRaises(SystemExit):
            auth.log_in_for_userkey()

    @patch('taktyk.auth.save_userkey')
    @patch('requests.post')
    def test_when_api_app_provided_check_if_userkey_is_set_and_saved(self, test_post,
                                                                     test_save_userkey):
        settings.ACCOUNTKEY = 'acckey123'
        settings.SECRETKEY = 'secret321'
        mock_resp = Mock()
        mock_resp.json.return_value = {'userkey': 'user123key'}
        test_post.return_value = mock_resp
        auth.log_in_for_userkey()
        self.assertEqual(settings.USERKEY, 'user123key')
        test_save_userkey.assert_called_with('user123key')

    @patch('requests.post')
    @patch('getpass.getpass')
    def test_when_ask_for_password_check_if_correct_post_args(self, test_getpass, test_post):
        settings.ACCOUNTKEY = None
        test_getpass.return_value = 'pass25word'
        data = {'login': 'login123', 'password': 'pass25word'}
        headers = {}
        mock_resp = Mock()
        mock_resp.json.return_value = {'userkey': 'user123key'}
        test_post.return_value = mock_resp
        auth.log_in_for_userkey()
        test_post.assert_called_with(self.url, data=data, headers=headers)

    @patch('taktyk.auth.get_username')
    @patch('requests.post')
    @patch('getpass.getpass')
    def test_when_ask_for_password_check_if_continues_on_error(self, test_getpass, test_post, test_username):
        test_username.return_value = 'login123'
        settings.ACCOUNTKEY = None
        test_getpass.return_value = 'pass25word'
        mock_resp = Mock()
        mock_resp.json.side_effect = [{}, {'userkey': 'user123key'}]  # first time call - KeyError
        test_post.return_value = mock_resp
        auth.log_in_for_userkey()
        self.assertEqual(test_post.call_count, 2)

    @patch('taktyk.auth.save_userkey')
    @patch('requests.post')
    @patch('getpass.getpass')
    def test_when_ask_for_password_check_if_userkey_is_set_and_saved(self, test_getpass, test_post,
                                                                     test_save_userkey):
        test_getpass.return_value = 'pass25word'
        mock_resp = Mock()
        mock_resp.json.return_value = {'userkey': 'user123key'}
        test_post.return_value = mock_resp
        auth.log_in_for_userkey()
        self.assertEqual(settings.USERKEY, 'user123key')
        test_save_userkey.assert_called_with('user123key')


@patch('requests.get')
class GetTokenTest(unittest.TestCase):
    def test_if_requests_get_called_with_right_url(self, test_get):
        url = settings.LOGIN_URL
        mock_get = Mock()
        mock_get.text = '<html><div id="__token" value="token123"></div></html>'
        test_get.return_value = mock_get
        auth.get_token()
        test_get.assert_called_with(url)

    def test_when_token_found(self, test_get):
        mock_get = Mock()
        mock_get.text = '<html><div id="__token" value="token123"></div></html>'
        test_get.return_value = mock_get
        self.assertEqual(auth.get_token(), 'token123')

    def test_when_token_not_found(self, test_get):
        mock_get = Mock()
        mock_get.text = '<html></html>'
        test_get.return_value = mock_get
        with self.assertRaises(SystemExit):
            auth.get_token()


class LogInForSessionTest(unittest.TestCase):
    def setUp(self):
        self.patcher1 = patch('taktyk.auth.get_token')
        self.test_get_token = self.patcher1.start()
        self.patcher2 = patch('requests.session')
        self.test_session = self.patcher2.start()
        self.test_get_token.return_value = 'token123'
        settings.USERNAME = 'name444'
        self.login_url = settings.LOGIN_URL
        self.wykop_url = settings.WYKOP_URL

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()

    @patch('getpass.getpass')
    def test_if_post_args_are_correct(self, test_getpass):
        test_getpass.return_value = 'pass25word'
        data = {'user[username]': 'name444',
                'user[password]': 'pass25word',
                '__token': 'token123'}
        mock_get = Mock()
        mock_get.text = '<html><img class="avatar" alt="name444"></html>'
        session_mock = Mock()
        session_mock.get.return_value = mock_get
        self.test_session.return_value = session_mock
        auth.log_in_for_session()
        session_mock.post.assert_called_with(self.login_url, data=data)

    @patch('getpass.getpass')
    def test_when_login_found(self, test_getpass):
        mock_get = Mock()
        mock_get.text = '<html><img class="avatar" alt="name444"></html>'
        session_mock = Mock()
        session_mock.get.return_value = mock_get
        self.test_session.return_value = session_mock
        self.assertEqual(session_mock, auth.log_in_for_session())

    @patch('taktyk.auth.get_username')
    @patch('getpass.getpass')
    def test_when_login_not_found(self, test_getpass, test_get_username):
        test_get_username.return_value = 'name444'
        mock_get1 = Mock()
        mock_get1.text = '<html></html>'  # AttributeError
        mock_get2 = Mock()
        mock_get2.text = '<html><img class="avatar" alt="name444"></html>'
        session_mock = Mock()
        session_mock.get.side_effect = [mock_get1, mock_get2]
        self.test_session.return_value = session_mock
        auth.log_in_for_session()
        self.assertEqual(test_getpass.call_count, 2)

    @patch('taktyk.auth.get_username')
    @patch('getpass.getpass')
    def test_when_usernames_dont_match(self, test_getpass, test_get_username):
        test_get_username.return_value = 'name444'
        mock_get1 = Mock()
        mock_get1.text = '<html><img class="avatar" alt="wrongusername"></html>'
        mock_get2 = Mock()
        mock_get2.text = '<html><img class="avatar" alt="name444"></html>'
        session_mock = Mock()
        session_mock.get.side_effect = [mock_get1, mock_get2]
        self.test_session.return_value = session_mock
        auth.log_in_for_session()
        self.assertEqual(test_getpass.call_count, 2)

    @patch('getpass.getpass')
    def test_if_login_lowered(self, test_getpass):
        settings.USERNAME = 'Name007'
        mock_get = Mock()
        mock_get.text = '<html><img class="avatar" alt="nAME007"></html>'
        session_mock = Mock()
        session_mock.get.return_value = mock_get
        self.test_session.return_value = session_mock
        self.assertEqual(session_mock, auth.log_in_for_session())


class SetUserkeyTest(unittest.TestCase):
    @patch('taktyk.auth.is_key_valid')
    def test_if_userkey_exist_and_valid(self, test_is_key_valid):
        settings.USERKEY = 'user123key'
        test_is_key_valid.return_value = True
        self.assertTrue(auth.set_userkey())

    @patch('taktyk.auth.is_key_valid')
    def test_if_userkey_exist_and_invalid(self, test_is_key_valid):
        settings.USERKEY = 'user123key'
        test_is_key_valid.return_value = False
        with self.assertRaises(SystemExit):
            auth.set_userkey()

    @patch('taktyk.auth.get_and_check_saved_userkey')
    def test_if_userkey_doesnt_exist_and_valid_from_file(self, test_get_and_check_saved_userkey):
        settings.USERKEY = None
        test_get_and_check_saved_userkey.return_value = 'UserkeyFromFile'
        auth.set_userkey()
        self.assertEqual(settings.USERKEY, 'UserkeyFromFile')

    @patch('taktyk.auth.log_in_for_userkey')
    @patch('taktyk.auth.get_and_check_saved_userkey')
    def test_if_userkey_doesnt_exist_and_invalid_from_file(self, test_get_and_check_saved_userkey,
                                                           test_log_in_for_userkey):
        settings.USERKEY = None
        test_get_and_check_saved_userkey.return_value = False
        auth.set_userkey()
        self.assertTrue(test_log_in_for_userkey.called)


class SaveUserkeyTest(unittest.TestCase):
    def setUp(self):
        settings.USER_FILES_PATH = os.path.join(settings.SAVE_PATH, 'tests')
        settings.USERKEY_FILE = 'test_userkey.txt'
        self.file_path = os.path.join(settings.USER_FILES_PATH, settings.USERKEY_FILE)

    def tearDown(self):
        os.remove(self.file_path)

    def test_if_data_in_file_is_saved(self):
        auth.save_userkey('userkey12345')
        with open(self.file_path, 'r') as file:
            saved_data = json.load(file)
        self.assertEqual(saved_data['userkey'], 'userkey12345')
        self.assertTrue(str(datetime.now() + timedelta(hours=22)) < saved_data['expire'])


class GetSavedUserkeyFromFile(unittest.TestCase):
    def setUp(self):
        settings.USER_FILES_PATH = os.path.join(settings.SAVE_PATH, 'tests')
        settings.USERKEY_FILE = 'test_userkey.txt'
        self.file_path = os.path.join(settings.USER_FILES_PATH, settings.USERKEY_FILE)

    def tearDown(self):
        if os.path.isfile(self.file_path):
            os.remove(self.file_path)

    def test_read_data_file_exist(self):
        data = {
            'userkey': '1234userkey',
            'expire': 'somedate'
        }
        with open(self.file_path, 'w') as file:
            json.dump(data, file)

        saved_data = auth.get_saved_userkey_from_file()
        self.assertEqual(data, saved_data)

    def test_when_file_doesnt_exist(self):
        self.assertEqual({}, auth.get_saved_userkey_from_file())


class GetAndCheckSavedUserkeyTest(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('taktyk.auth.get_saved_userkey_from_file')
        self.test_get_userkey = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_when_userkey_from_file_ok(self):
        self.test_get_userkey.return_value = {'userkey': 'u71234key',
                                         'expire': str(datetime.now() + timedelta(hours=23))}
        self.assertEqual(auth.get_and_check_saved_userkey(), 'u71234key')

    def test_when_userkey_from_file_expired(self):
        self.test_get_userkey.return_value = {'userkey': 'u71234key',
                                         'expire': str(datetime.now() + timedelta(hours=-10))}
        self.assertFalse(auth.get_and_check_saved_userkey())

    def test_when_no_file(self):
        self.test_get_userkey.return_value = {}
        self.assertFalse(auth.get_and_check_saved_userkey())


class IsKeyValidTest(unittest.TestCase):
    @patch('requests.get')
    def test_if_appkey_or_userkey_ok(self, test_get):
        mock_get = Mock()
        mock_get.text = 'some message probably json'
        test_get.return_value = mock_get
        self.assertTrue(auth.is_key_valid('app123key'))
        self.assertTrue(auth.is_key_valid('app123key', 'userkey123'))

    @patch('requests.get')
    def test_if_appkey_or_userkey_invalid(self, test_get):
        mock_get = Mock()
        mock_get.text = 'error in message'
        test_get.return_value = mock_get
        self.assertFalse(auth.is_key_valid('app123key'))
        self.assertFalse(auth.is_key_valid('app123key', 'userkey123'))

    @patch('requests.get')
    def test_if_get_called_with_correct_args(self, test_get):
        settings.SECRETKEY = 'secret'
        url = settings.API_CHECK_URL
        mock_get = Mock()
        mock_get.text = 'message'
        test_get.return_value = mock_get
        auth.is_key_valid('app123key')
        url1 = url + 'app123key'
        headers = auth.apisign(url1, 'secret')
        test_get.assert_called_with(url1, headers=headers)
        auth.is_key_valid('app123key', 'user555key')
        url2 = url + 'app123key' + '/userkey/' + 'user555key'
        headers = auth.apisign(url2, 'secret')
        test_get.assert_called_with(url2, headers=headers)


class ApisingTest(unittest.TestCase):
    def test_with_no_secret(self):
        self.assertEqual({}, auth.apisign('someurl'))

    def test_with_secret_sorted(self):
        url = 'www.test.test'
        secret = 'supersecret'
        kwargs = {'login': 'alogin', 'acckey': 'nextkey'}
        m = hashlib.md5()
        post = 'nextkey,alogin'  # sorted by key name
        m.update(secret.encode() + url.encode() + post.encode())
        self.assertEqual({'apisign': m.hexdigest()}, auth.apisign(url, secret, **kwargs))

    def test_with_secret_unsorted(self):
        url = 'www.test.test'
        secret = 'supersecret'
        kwargs = {'login': 'alogin', 'acckey': 'nextkey'}
        m = hashlib.md5()
        post = 'alogin,nextkey'  # unsorted
        m.update(secret.encode() + url.encode() + post.encode())
        self.assertNotEqual({'apisign': m.hexdigest()}, auth.apisign(url, secret, **kwargs))
