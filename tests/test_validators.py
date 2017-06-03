import os
import sys
import unittest
from unittest.mock import patch, Mock, MagicMock


sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.commands.validators import userkey_validator, source_validator, is_text_file, ids_validator


class UserkeyValidatorTest(unittest.TestCase):
    def setUp(self):
        patcher = patch('taktyk.auth.is_key_valid')
        self.mock_is_key_valid = patcher.start()
        self.addCleanup(patcher.stop)

    def test_if_userkey_valid(self):
        self.mock_is_key_valid.return_value = True
        self.assertEqual('user123key', userkey_validator('user123key'))

    def test_if_userkey_invalid(self):
        self.mock_is_key_valid.return_value = False
        with self.assertRaises(ValueError):
            userkey_validator('user123key')


class SourceValidatorTest(unittest.TestCase):
    def setUp(self):
        patcher1 = patch('os.path.isfile')
        patcher2 = patch('os.path.isdir')
        self.mock_isfile = patcher1.start()
        self.mock_isdir = patcher2.start()
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)

    def test_when_file_or_folder_doesnt_exist(self):
        self.mock_isfile.return_value = False
        self.mock_isdir.return_value = False
        with self.assertRaises(ValueError):
            source_validator('path_to_source')

    @patch('taktyk.commands.validators.is_text_file')
    def test_when_file_exist_but_is_not_a_text_file(self, mock_is_text_file):
        self.mock_isfile.return_value = True
        mock_is_text_file.return_value = False
        with self.assertRaises(ValueError):
            source_validator('path_to_source')

    @patch('taktyk.commands.validators.is_text_file')
    def test_when_file_exist_and_is_a_text_file(self, mock_is_text_file):
        self.mock_isfile.return_value = True
        mock_is_text_file.return_value = True
        self.assertEqual({'file': 'path_to_source'}, source_validator('path_to_source'))

    @patch('os.listdir')
    def test_when_folder_exist_but_empty(self, mock_listdir):
        self.mock_isfile.return_value = False
        self.mock_isdir.return_value = True
        mock_listdir.return_value = False
        with self.assertRaises(ValueError):
            source_validator('path_to_source')

    @patch('os.listdir')
    def test_when_folder_exist_and_not_empty(self, mock_listdir):
        self.mock_isfile.return_value = False
        self.mock_isdir.return_value = True
        mock_listdir.return_value = True
        self.assertEqual({'dir': 'path_to_source'}, source_validator('path_to_source'))


class IsTextFileTest(unittest.TestCase):
    def setUp(self):
        patcher = patch('builtins.open')
        self.test_open = patcher.start()
        self.addCleanup(patcher.stop)
        pass

    def test_when_oserror_raised(self):
        m_open = MagicMock()
        m_open.__enter__ = Mock(side_effect=OSError)
        m_open.__exit__ = Mock()
        self.test_open.return_value = m_open
        self.assertFalse(is_text_file('file'))

    def test_when_valueerror_raised(self):
        m_open = MagicMock()
        m_open.__enter__ = Mock(side_effect=ValueError)
        m_open.__exit__ = Mock()
        self.test_open.return_value = m_open
        self.assertFalse(is_text_file('file'))

    def test_when_no_exception_caught(self):
        self.assertTrue(is_text_file('file'))


class IdsValidatorTest(unittest.TestCase):
    def test_when_no_ids(self):
        ids = ''
        with self.assertRaises(ValueError):
            ids_validator(ids)

    def test_if_output_correct(self):
        ids = '123 123d12312 1288 ssdf 9fsdfsf111'
        self.assertEqual({'123', '1288'}, ids_validator(ids))

    def test_if_no_duplicates(self):
        ids = '1 1 33 2 33\n sdfsdf 123sds 12'
        self.assertEqual({'1', '2', '33', '12'}, ids_validator(ids))
