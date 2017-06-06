import os
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk import settings
from taktyk.utils import Decision, ConfigFile


class DecisionTest(unittest.TestCase):
    def setUp(self):
        patcher = patch('builtins.input')
        self.mock_input = patcher.start()
        self.addCleanup(patcher.stop)
        self.dec = Decision('')

    def test_if_options_are_lowered(self):
        self.dec.options = {'T': 1, 'N': 2}
        self.assertTrue('t' in self.dec.options.keys())
        self.assertTrue('n' in self.dec.options.keys())

    def test_run_if_input_in_options_without_func(self):
        self.dec.options = {'1': 'result'}
        self.mock_input.return_value = '1'
        self.assertEqual(self.dec.run(), 'result')

    def test_run_if_input_in_options_with_func(self):
        func = Mock(return_value='func_result')
        self.dec.options = {'1': func}
        self.mock_input.return_value = '1'
        self.assertEqual(self.dec.run(), 'func_result')
        self.assertTrue(func.call_count == 1)

    def test_run_if_input_in_options_with_func_with_args(self):
        def func(x, y):
            return x + y
        self.dec.options = {'Y': {func: (10, 5)}}
        self.mock_input.return_value = 'y'
        self.assertEqual(self.dec.run(), 15)

    def test_when_validator_is_passed(self):
        self.dec.validator = lambda x: x
        self.mock_input.return_value = 'validated data'
        self.assertEqual(self.dec.run(), 'validated data')

    def test_when_validation_fails(self):
        def validator(data_to_validate):
            data_to_validate = int(data_to_validate)
            if data_to_validate > 10:
                raise ValueError('Number greater than 10')
            return data_to_validate

        self.dec.validator = validator
        self.mock_input.side_effect = ['20', '5']
        self.assertEqual(self.dec.run(), 5)

    def test_when_user_input_doesnt_match_options(self):
        self.dec.options = {'n': 'n', 'y': 'y'}
        self.mock_input.side_effect = ['wrong input', 'second time', 'y']
        self.assertEqual(self.dec.run(), 'y')
        self.assertEqual(self.mock_input.call_count, 3)


class ConfigFileTest(unittest.TestCase):
    def setUp(self):
        self.config = ConfigFile()
        self.config.file_path = os.path.join(settings.SAVE_PATH, 'tests', 'test_config.ini')

        def cleanup():
            if os.path.isfile(self.config.file_path):
                os.remove(self.config.file_path)

        self.cleanup = cleanup

    def test_file_creation(self):
        self.config.set_up()
        with open(self.config.file_path) as file:
            content = file.read()

        for section, options in self.config.template:
            self.assertTrue(section in content)
            for option in options:
                self.assertTrue(option[0] in content)

        self.cleanup()

    def test_if_config_is_applied_username_password(self):
        self.config.set_up()
        self.config.config['DANE LOGOWANIA']['username'] = 'test_username'
        self.config.config['DANE LOGOWANIA']['password'] = 'test_pass'
        self.config.create_configfile()
        self.config.set_up()
        self.assertEqual('test_username', settings.USERNAME)
        self.assertEqual('test_pass', settings.PASSWORD)
        self.cleanup()

    def test_if_config_is_applied_wykop_api(self):
        self.config.set_up()
        self.config.config['WykopAPI']['appkey'] = 'test_appkey'
        self.config.config['WykopAPI']['secretkey'] = 'test_secret'
        self.config.config['WykopAPI']['accountkey'] = 'test_acckey'
        self.config.config['WykopAPI']['userkey'] = 'test_userkey'
        self.config.create_configfile()
        self.config.set_up()
        self.assertEqual('test_appkey', settings.APPKEY)
        self.assertEqual('test_secret', settings.SECRETKEY)
        self.assertEqual('test_acckey', settings.ACCOUNTKEY)
        self.assertEqual('test_userkey', settings.USERKEY)
        self.cleanup()

    def test_if_config_is_applied_static_args(self):
        self.config.set_up()
        self.config.config['ARGUMENTY']['static_args'] = '-n --scrape --selenium chrome'
        self.config.create_configfile()
        self.config.set_up()
        self.assertEqual(['-n', '--scrape', '--selenium', 'chrome'], settings.STATIC_ARGS)
        self.cleanup()

    def test_if_config_is_applied_exts(self):
        self.config.set_up()
        self.config.config['POBIERANE ROZSZERZENIA']['exts'] = '.jpg'
        self.config.create_configfile()
        self.config.set_up()
        self.assertEqual(['.jpg'], settings.EXTS)
        self.cleanup()
