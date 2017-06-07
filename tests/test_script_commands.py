import os
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk import settings
from taktyk.commands.script_commands import CheckForUpdate, DBHandler, ConfigureCommand
from taktyk.entrygenerators import APIMethod, ScrapeMethod
from taktyk.strategies import APIStrategy, SessionStrategy


class ConfigureCommandTest(unittest.TestCase):
    @patch('taktyk.commands.script_commands.is_key_valid')
    def test_set_strategy_and_method_when_key_valid(self, mock_is_key_valid):
        mock_is_key_valid.return_value = True
        ConfigureCommand.set_strategy_and_method()
        self.assertEqual(APIStrategy, settings.STRATEGY)
        self.assertEqual(APIMethod, settings.METHOD)

    @patch('taktyk.commands.script_commands.is_key_valid')
    def test_set_strategy_and_method_when_key_invalid(self, mock_is_key_valid):
        mock_is_key_valid.return_value = False
        ConfigureCommand.set_strategy_and_method()
        self.assertEqual(SessionStrategy, settings.STRATEGY)
        self.assertEqual(ScrapeMethod, settings.METHOD)
        self.assertTrue(settings.SCRAPE)

    @patch('taktyk.commands.script_commands.ConfigureCommand.set_strategy_and_method')
    def test_execute(self, mock_set_strategy_and_method):
        ConfigureCommand().execute()
        self.assertTrue(mock_set_strategy_and_method.called)


class CheckForUpdateTest(unittest.TestCase):
    def setUp(self):
        self.cfu = CheckForUpdate()
        self.cfu.local_version = '1.0.0'

    @patch('taktyk.commands.script_commands.Request.get')
    def test_get_github_version(self, mock_get):
        response = Mock()
        response.url = 'https://github.com/kosior/taktyk/releases/tag/2.0.0'
        mock_get.return_value = response
        self.assertEqual('2.0.0', self.cfu.get_github_version())

    @patch('taktyk.commands.script_commands.Request.get')
    def test_get_github_version_if_attribute_error(self, mock_get):
        mock_get.side_effect = AttributeError
        with self.assertRaises(AttributeError):
            self.cfu.get_github_version()

    def test_is_new_version(self):
        self.cfu.get_github_version = lambda: '2.0.0'
        self.assertTrue(self.cfu.is_new_version())
        self.cfu.get_github_version = lambda: '0.9.9'
        self.assertFalse(self.cfu.is_new_version())

    def test_execute(self):
        notify = Mock()
        self.cfu.notify = notify
        self.cfu.is_new_version = lambda: True
        self.cfu.execute()
        self.assertTrue(notify.called)


class DBHandlerTest(unittest.TestCase):
    def setUp(self):
        patcher = patch('taktyk.commands.script_commands.database_list')
        self.mock_db_list = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_db_list.return_value = []
        self.dbh = DBHandler()

    def test_set_db_name(self):
        DBHandler.set_db_name('test_name.db')
        self.assertEqual('test_name.db', settings.DB_NAME)

    @patch('taktyk.commands.script_commands.DB.create')
    def test_execute_when_no_db(self, mock_create_db):
        self.dbh.execute()
        self.assertTrue(mock_create_db.called)

    def test_execute_when_one_db(self):
        self.dbh.db_list = ['test_db.db']
        self.dbh.db_len = 1
        self.dbh.execute()
        self.assertEqual('test_db.db', settings.DB_NAME)

    @patch('taktyk.commands.script_commands.DBHandler.choose')
    def test_execute_when_two_or_more_dbs(self, mock_choose):
        self.dbh.db_len = 2
        self.dbh.execute()
        self.assertTrue(mock_choose.called)
