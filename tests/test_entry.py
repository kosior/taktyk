import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.entry import Entry
from taktyk import settings


class EntryTest(unittest.TestCase):
    def setUp(self):
        self.entry = Entry(123, 'author', 'date', 'body', 'body_html', 'url', 'plus', 'media_url',
                           'tags', 'is_nsfw', 'entry_id', 'type_')

    def test_attrs_gen(self):
        args = (123, 'author', 'date', 'body', 'body_html', 'url', 'plus', 'media_url', 'tags',
                'is_nsfw', 'entry_id', 'type_')

        self.assertEqual(tuple(self.entry.attrs_gen()), args[:11])
        self.assertEqual(tuple(self.entry.__iter__()), args[:11])

    def test_str(self):
        self.assertEqual('entry_id_123', str(self.entry))
        self.entry.entry_id = None
        self.assertEqual('123', str(self.entry))

    def test_download_info(self):
        d_info = {'id_': 'entry_id_123', 'media_url': 'media_url', 'is_nsfw': 'is_nsfw',
                  'local_file_path': ''}
        self.assertEqual(self.entry.download_info(), d_info)

    def test_comments_count_with_entry_id(self):
        self.assertIsNone(self.entry.comments_count)

    @patch('taktyk.db.DB.count_comments')
    def test_comments_count_without_entry_id(self, mock_comments_count):
        self.entry.entry_id = None
        mock_comments_count.return_value = 125
        self.assertEqual(125, self.entry.comments_count)

    def test_media_ext_when_media_url_is_none(self):
        self.entry.media_url = ''
        self.assertIsNone(self.entry.media_ext)

    def test_media_ext_when_media_url_has_ext(self):
        self.entry.media_url = 'somemediaurl.jpg'
        self.assertEqual('.jpg', self.entry.media_ext)

    def test_media_ext_when_media_url_has_questionmark_inside(self):
        self.entry.media_url = 'somemediaurl.gif?someweirdending'
        self.assertEqual('.gif', self.entry.media_ext)

    def test_media_ext_when_media_url_is_gfycat(self):
        self.entry.media_url = 'http://gfycat.com/asdf8df7s7'
        self.assertEqual('.webm', self.entry.media_ext)

    def test_media_ext_when_no_ext_in_media_url(self):
        self.entry.media_url = 'www.youtube.com/avideo'
        self.assertFalse(self.entry.media_ext)

    def test_local_file_path_when_no_media_url_or_ext(self):
        self.entry.media_url = ''
        self.assertFalse(self.entry.local_file_path)
        self.entry.media_url = 'www.youtube.com/avideo'
        self.assertFalse(self.entry.local_file_path)

    def test_local_file_path_when_is_nsfw_is_true_and_not_comment(self):
        self.entry.is_nsfw = True
        self.entry.entry_id = None
        self.entry.media_url = 'url/with/ext.png'
        settings.FILES_DIR_NAME = 'dir'
        expected_path = os.path.join('dir', 'nsfw', '123.png')
        self.assertEqual(expected_path, self.entry.local_file_path)

    def test_local_file_path_when_is_nsfw_is_true_and_is_comment(self):
        self.entry.is_nsfw = True
        self.entry.entry_id = '90'
        self.entry.media_url = 'url/with/ext.jpg'
        settings.FILES_DIR_NAME = 'dir'
        expected_path = os.path.join('dir', 'nsfw', 'komentarze', '90_123.jpg')
        self.assertEqual(expected_path, self.entry.local_file_path)

    def test_local_file_path_when_is_nsfw_is_false_and_not_comment(self):
        self.entry.is_nsfw = False
        self.entry.entry_id = None
        self.entry.media_url = 'url/with/ext.webm'
        settings.FILES_DIR_NAME = 'dir'
        expected_path = os.path.join('dir', '123.webm')
        self.assertEqual(expected_path, self.entry.local_file_path)

    def test_local_file_path_when_is_nsfw_is_false_and_is_comment(self):
        self.entry.is_nsfw = False
        self.entry.entry_id = '55'
        self.entry.media_url = 'url/with/ext.gif'
        settings.FILES_DIR_NAME = 'dir'
        expected_path = os.path.join('dir', 'komentarze', '55_123.gif')
        self.assertEqual(expected_path, self.entry.local_file_path)
