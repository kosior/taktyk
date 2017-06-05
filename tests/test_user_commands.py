import os
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk import settings
from taktyk.commands.user_commands import NewCommand, PdkCommand, SeleniumCommand, SessionCommand, \
    FileSourceCommand, HtmlCommand, IdsCommand, ScrapeCommand, SkipCommand, NsfwCommand, \
    CommentsCommand
from taktyk.entrygenerators import ScrapeMethod
from taktyk.strategies import SeleniumStrategy, SessionStrategy, SourceStrategy, APIStrategy


class NewCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('new', NewCommand.name)

    @patch('taktyk.commands.user_commands.DB.ask_and_create')
    def test_execute(self, mock_create_new):
        NewCommand().execute()
        self.assertTrue(mock_create_new.call_count == 1)


class PdkCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('pdk', PdkCommand.name)

    @patch('taktyk.commands.user_commands.Decision')
    def test_execute(self, mock_decision):
        instance = Mock()
        instance.run.return_value = 'userkey'
        mock_decision.return_value = instance
        PdkCommand().execute()
        self.assertEqual(settings.USERKEY, 'userkey')


class FileSourceCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('file', FileSourceCommand.name)

    @patch('taktyk.commands.user_commands.Decision')
    def test_execute(self, mock_decision):
        instance = Mock()
        instance.run.return_value = {'file': 'source'}
        mock_decision.return_value = instance
        FileSourceCommand().execute()
        self.assertEqual(settings.SOURCE, {'file': 'source'})
        self.assertEqual(settings.STRATEGY, SourceStrategy)


class SeleniumCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('selenium', SeleniumCommand.name)

    def test_execute(self):
        SeleniumCommand().execute('somebrowser')
        self.assertEqual(settings.STRATEGY, SeleniumStrategy)
        self.assertEqual(settings.BROWSER, 'somebrowser')


class SessionCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('session', SessionCommand.name)

    def test_execute(self):
        SessionCommand().execute()
        self.assertEqual(settings.STRATEGY, SessionStrategy)


class HtmlCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('html', HtmlCommand.name)

    @patch('taktyk.commands.user_commands.HtmlFile')
    def test_execute_when_arg_is_true(self, mock_html_file):
        with self.assertRaises(SystemExit):
            HtmlCommand().execute(arg=True)
        mock_html_file.assert_called_with(tag=None)

    @patch('taktyk.commands.user_commands.HtmlFile')
    def test_execute_when_arg_is_tag(self, mock_html_file):
        with self.assertRaises(SystemExit):
            HtmlCommand().execute(arg='programowanie')
        mock_html_file.assert_called_with(tag='programowanie')

    @patch('taktyk.commands.user_commands.HtmlFile.create')
    def test_execute_if_create_called(self, mock_create):
        with self.assertRaises(SystemExit):
            HtmlCommand().execute(arg=True)
        self.assertTrue(mock_create.called)


class CommentsCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('comments', CommentsCommand.name)

    @patch('taktyk.DB.get_ids')
    def test_execute(self, mock_get_ids):
        mock_get_ids.return_value = [1, 2, 3, 4]
        CommentsCommand().execute()
        self.assertTrue(settings.FULL_UPDATE)
        self.assertEqual(settings.SOURCE, {'ids': [1, 2, 3, 4]})
        self.assertEqual(settings.STRATEGY, SourceStrategy)
        mock_get_ids.assert_called_with('entry')


class NsfwCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('nsfw', NsfwCommand.name)

    def test_execute(self):
        NsfwCommand().execute()
        self.assertTrue(settings.NSFW_FILTER)


class SkipCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('skip', SkipCommand.name)

    def test_execute_when_arg_is_true(self):
        SkipCommand().execute(arg=True)
        self.assertTrue(settings.SKIP_FILES is True)

    def test_execute_when_arg_is_com(self):
        SkipCommand().execute(arg='com')
        self.assertTrue(settings.SKIP_FILES == 'com')


class ScrapeCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('scrape', ScrapeCommand.name)

    def test_execute(self):
        settings.STRATEGY = APIStrategy
        ScrapeCommand().execute()
        self.assertTrue(settings.SCRAPE)
        self.assertEqual(settings.STRATEGY, SessionStrategy)
        self.assertEqual(settings.METHOD, ScrapeMethod)


class IdsCommandTest(unittest.TestCase):
    def test_name(self):
        self.assertEqual('ids', IdsCommand.name)

    @patch('taktyk.commands.user_commands.Decision')
    def test_execute(self, mock_decision):
        instance = Mock()
        instance.run.return_value = (1, 2, 3, 44)
        mock_decision.return_value = instance
        IdsCommand().execute()
        self.assertEqual(settings.SOURCE, {'ids': (1, 2, 3, 44)})
        self.assertEqual(settings.STRATEGY, SourceStrategy)
