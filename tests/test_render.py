import os
import sys
import unittest
from contextlib import ContextDecorator
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk import settings
from taktyk.db import DB
from taktyk.entry import Entry
from taktyk.render import HtmlFile


class HtmlFileTest(unittest.TestCase):
    def setUp(self):
        self.date = 'date'
        self.html_name = 'taktyk-date.html'
        self.html_path = os.path.join(settings.SAVE_PATH, 'tests', self.html_name)

    def tearDown(self):
        if os.path.isfile(self.html_path):
            os.remove(self.html_path)

    def test_create_file_name_extension(self):
        self.assertEqual(HtmlFile().create_file_name()[-5:], '.html')

    @patch('time.strftime')
    def test_create_file_name_strftime_called(self, test_strftime):
        HtmlFile().create_file_name()
        self.assertTrue(test_strftime.called)

    @patch('time.strftime')
    def test_create_file_name_strftime_called(self, test_strftime):
        test_strftime.return_value = self.date
        self.assertEqual(HtmlFile().create_file_name(), self.html_name)

    def test_get_full_path(self):
        htmlfile = HtmlFile()
        htmlfile.user_files_path = 'path'
        htmlfile.create_file_name = Mock(return_value='file_name')
        self.assertEqual(htmlfile.get_full_path(), os.path.join('path', 'file_name'))

    def test_render_when_no_template(self):
        htmlfile = HtmlFile()
        htmlfile.templates_path = ''
        htmlfile.template_name = 'templatenotfound.html'
        with self.assertRaises(SystemExit):
            htmlfile.render([], [])

    @patch('time.strftime')
    @patch('taktyk.db.DB')
    @patch('taktyk.db.DB.count_tags')
    @patch('taktyk.db.DB.get_all_entries_with_comments')
    def test_create(self, mock_get_all_entries, mock_count_tags, mock_db, test_strftime):
        test_strftime.return_value = self.date
        tags = [('testtag1', 123), ('testtag2', 1), ('testtag3', 25)]
        mock_count_tags.return_value = tags
        entry_args = ('444', 'testauthor', 'testdate', '', 'testbody_html', 'testurl', '+1000',
                      'testmedia_url', 'testtags', '')
        sample_entry = Entry(*entry_args)
        mock_get_all_entries.return_value = [sample_entry]

        class MockConnect(ContextDecorator):
            def __enter__(self):
                pass

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        DB.Connect = MockConnect
        htmlfile = HtmlFile()
        htmlfile.user_files_path = os.path.join(settings.SAVE_PATH, 'tests')
        htmlfile.create()

        self.assertTrue(os.path.isfile(self.html_path))

        with open(self.html_path, 'r') as file:
            content = file.read()

        for tag, _ in tags:
            self.assertTrue(tag in content)
        for arg in entry_args:
            self.assertTrue(arg in content)
