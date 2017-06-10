import os
import sys
import unittest
from unittest.mock import patch, mock_open, Mock, call

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk import settings
from taktyk.strategies import Strategy, APIStrategy, SourceStrategy


class GetContentByIdsTest(unittest.TestCase):
    @patch('taktyk.strategies.HtmlContent.gen_html_entries_by_ids')
    def test_get_content_by_ids_when_scrape_true(self, mock_gen_html_entries_by_ids):
        settings.SCRAPE = True
        ids = [1, 2, 3]
        Strategy.get_content_by_ids(ids)
        mock_gen_html_entries_by_ids.assert_called_with(ids)

    @patch('taktyk.strategies.ApiContent.gen_entries_by_ids')
    def test_get_content_by_ids_when_scrape_true(self, mock_gen_entries_by_ids):
        settings.SCRAPE = False
        ids = [1, 2, 3]
        Strategy.get_content_by_ids(ids)
        mock_gen_entries_by_ids.assert_called_with(ids)


class ScrapePagesForIdsTest(unittest.TestCase):
    def setUp(self):
        settings.FAVORITES_URL_F = '{username}/page/'
        patcher = patch('taktyk.strategies.HtmlParser.find_ids_in_html')
        self.mock_find_ids_in_html = patcher.start()
        self.addCleanup(patcher.stop)

    def test_if_get_page_func_called(self):
        get_page_func = Mock()
        self.mock_find_ids_in_html.side_effect = [[1], [2], [3], None]
        Strategy.scrape_pages_for_ids('test_user', get_page_func)
        calls = [call('test_user/page/{}'.format(i)) for i in range(1, 5)]
        get_page_func.assert_has_calls(calls)

    def test_return_value(self):
        self.mock_find_ids_in_html.side_effect = [[1, 2], [3, 4], [5], None]
        ids = Strategy.scrape_pages_for_ids('test_user', Mock())
        self.assertEqual(ids, [1, 2, 3, 4, 5])


class ApiStrategyTest(unittest.TestCase):
    @patch('taktyk.strategies.ApiContent.gen_entries')
    @patch('taktyk.strategies.set_userkey')
    def test_execute(self, mock_set_userkey, mock_gen_entries):
        APIStrategy().execute()
        self.assertTrue(mock_set_userkey.called)
        self.assertTrue(mock_gen_entries.called)


class SourceStrategyTest(unittest.TestCase):
    def setUp(self):
        patcher = patch('taktyk.strategies.SourceStrategy.get_content_by_ids')
        self.mock_get_content_by_ids = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_get_content_by_ids.return_value = 'generator'

    @patch('taktyk.strategies.SourceStrategy.get_ids_from_file')
    def test_when_source_is_file(self, mock_get_ids_from_file):
        settings.SOURCE = {'file': 'file_path'}
        ids = [1, 2, 3]
        mock_get_ids_from_file.side_effect = [ids, []]
        result = SourceStrategy().execute()
        self.assertEqual(result, 'generator')
        self.mock_get_content_by_ids.assert_called_with(ids)
        mock_get_ids_from_file.assert_called_with('file_path')
        with self.assertRaises(SystemExit):
            SourceStrategy().execute()

    @patch('taktyk.strategies.SourceStrategy.get_ids_from_dir')
    def test_when_source_is_directory(self, mock_get_ids_from_dir):
        settings.SOURCE = {'dir': 'dir_path'}
        ids = [1, 2, 3]
        mock_get_ids_from_dir.side_effect = [ids, []]
        result = SourceStrategy().execute()
        self.assertEqual(result, 'generator')
        self.mock_get_content_by_ids.assert_called_with(ids)
        mock_get_ids_from_dir.assert_called_with('dir_path')
        with self.assertRaises(SystemExit):
            SourceStrategy().execute()

    def test_when_ids_are_from_user(self):
        ids = [1, 2, 3]
        settings.SOURCE = {'ids': ids}
        result = SourceStrategy().execute()
        self.assertEqual(result, 'generator')
        self.mock_get_content_by_ids.assert_called_with(ids)
        settings.SOURCE = {'ids': []}
        with self.assertRaises(SystemExit):
            SourceStrategy().execute()

    def test_get_ids_from_file(self):
        read_data = 'https://www.wykop.pl/wpis/120/someothernumber555 25 333 90invalid 25,10000,77'
        with patch('builtins.open', mock_open(read_data=read_data), create=True):
            ids = SourceStrategy.get_ids_from_file('fakepath')
        self.assertEqual(len(ids), 5)
        for id_ in ['120', '25', '333', '10000', '77']:
            self.assertTrue(id_ in ids)

    def test_get_ids_from_file_when_no_file(self):
        self.assertEqual([], SourceStrategy.get_ids_from_file('wrongpath'))

    @patch('taktyk.strategies.SourceStrategy.get_ids_from_file')
    @patch('taktyk.strategies.HtmlParser.find_ids_in_html')
    @patch('os.listdir')
    def test_get_ids_from_dir(self, mock_listdir, mock_find_ids_in_html, mock_get_ids_from_file):
        mock_listdir.return_value = ['test1.html', 'test2.htm', 'test3.txt']
        mock_find_ids_in_html.side_effect = [[1, 2, 3, 6], [4, 5, 6]]
        mock_get_ids_from_file.return_value = [7, 8, 9, 1]
        with patch('builtins.open', mock_open(), create=True):
            ids = SourceStrategy.get_ids_from_dir('testpath')
        self.assertEqual(len(ids), 9)
        for id_ in range(1, 10):
            self.assertTrue(id_ in ids)
