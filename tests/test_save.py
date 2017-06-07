import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk import settings
from taktyk.save import Save


class SaveTest(unittest.TestCase):
    def setUp(self):
        settings.EXTS = ['.jpg']
        id_ = 123
        media_url = 'http://url.com/file.jpg'
        is_nsfw = False
        local_file_path = '123.jpg'
        self.save = Save(id_, media_url, is_nsfw, local_file_path, cwd='test')

    @patch('os.path.exists')
    def test_get_path_when_path_exist(self, mock_exists):
        mock_exists.return_value = True
        path = self.save.get_path()
        self.assertEqual(os.path.join('test', '123.jpg'), path)

    @patch('os.path.exists')
    def test_get_path_when_path_doesnt_exist(self, mock_exists):
        mock_exists.return_value = False
        path = self.save.get_path()
        self.assertIsNone(path)

    def test_get_ext_if_ext_in_settings(self):
        ext = self.save.get_ext()
        self.assertEqual('.jpg', ext)

    def test_get_ext_if_ext_not_in_settings(self):
        self.save.file_name = '123.gif'
        ext = self.save.get_ext()
        self.assertIsNone(ext)

    @patch('taktyk.save.Request.get_json')
    def test_get_gfycat_url_when_gfycat_exist(self, mock_get_json):
        self.save.media_url = 'https://gfycat.com/gfyname'
        mock_get_json.return_value = {'gfyItem': {'webmUrl': 'test_webm_url'}}
        self.assertEqual('test_webm_url', self.save.get_gfycat_url())

    @patch('taktyk.save.Save.save_to_text_file')
    @patch('taktyk.save.Request.get_json')
    def test_get_gfycat_url_when_gfycat_exist(self, mock_get_json, mock_save_to_text_file):
        self.save.media_url = 'https://gfycat.com/gfyname'
        mock_get_json.side_effect = ValueError
        self.assertIsNone(self.save.get_gfycat_url())
        self.assertTrue(mock_save_to_text_file.called)

    @patch('taktyk.save.Save.save_to_text_file')
    def test_get_file_url_when_no_ext(self, mock_save_to_text_file):
        self.save._ext = None
        self.assertIsNone(self.save.get_file_url())
        self.assertTrue(mock_save_to_text_file.called)

    @patch('taktyk.save.Save.get_gfycat_url')
    def test_get_file_url_when_ext_is_webm(self, mock_get_gfycat_url):
        mock_get_gfycat_url.return_value = 'gfy_url'
        self.save.media_url = 'https://gfycat.com/gfyname'
        self.save._ext = '.webm'
        self.assertEqual('gfy_url', self.save.get_file_url())

    def test_get_file_url_when_ext_present_but_not_webm(self):
        self.save.media_url = 'media_url'
        self.save._ext = '.jpg'
        self.assertEqual('media_url', self.save.get_file_url())

    def test_nsfw_consistent(self):
        settings.NSFW_FILTER = True
        self.assertFalse(Save(1, 'file.jpg', is_nsfw=True, local_file_path='1.jpg').nsfw_consistent)
        settings.NSFW_FILTER = True
        self.assertTrue(Save(1, 'file.jpg', is_nsfw=False, local_file_path='1.jpg').nsfw_consistent)
        settings.NSFW_FILTER = False
        self.assertTrue(Save(1, 'file.jpg', is_nsfw=True, local_file_path='1.jpg').nsfw_consistent)
        settings.NSFW_FILTER = False
        self.assertTrue(Save(1, 'file.jpg', is_nsfw=False, local_file_path='1.jpg').nsfw_consistent)

    def test_save_when_no_url(self):
        self.save.url = None
        self.assertIsNone(self.save.save())

    def test_save_when_nsfw_inconsistent(self):
        self.save.nsfw_consistent = False
        self.assertIsNone(self.save.save())

    @patch('os.path.exists')
    def test_save_when_file_exists(self, mock_exists):
        mock_exists.return_value = True
        self.save.url = 'url'
        self.save.nsfw_consistent = True
        self.assertTrue(self.save.save())

    @patch('taktyk.save.Save.save_single_file')
    @patch('os.path.exists')
    def test_save_when_file_doesnt_exists(self, mock_exists, mock_save_single_file):
        mock_exists.side_effect = [True, False]
        mock_save_single_file.return_value = 'mock_return'
        self.save.url = 'url'
        self.save.nsfw_consistent = True
        self.assertEqual('mock_return', self.save.save())

    @patch('os.path.exists')
    def test_save_when_full_path_is_none(self, mock_exists):
        mock_exists.return_value = False
        self.save.url = 'url'
        self.save.nsfw_consistent = True
        self.assertFalse(self.save.save())
