import os
import sys
import unittest
from unittest.mock import patch, Mock

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.request import Request


class RequestGetTest(unittest.TestCase):
    def setUp(self):
        patcher = patch('requests.get')
        self.mock_requests_get = patcher.start()
        self.addCleanup(patcher.stop)

    def test_if_kwargs_are_passed_to_requests_get(self):
        url = 'http://url.com'
        Request.get(url, timeout=25, stream=True)
        self.mock_requests_get.assert_called_with(url, timeout=25, stream=True)

    def test_when_no_internet_conection(self):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.ConnectionError
        self.mock_requests_get.return_value = mock_response
        with self.assertRaises(SystemExit):
            Request.get('')

    @patch('logging.error')
    def test_when_response_not_200_and_exit_False_and_msg_true(self, mock_log_err):
        mock_log_err.return_value = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        self.mock_requests_get.return_value = mock_response
        self.assertIsNone(Request.get('', exit_=False, msg='samplemsg'))
        mock_log_err.assert_called_with('samplemsg')

    def test_when_response_not_200_and_exit_true_no_msg(self):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        self.mock_requests_get.return_value = mock_response
        with self.assertRaises(SystemExit):
            Request.get('', exit_=True)

    def test_return_value_when_response_correct(self):
        mock_response = Mock()
        self.mock_requests_get.return_value = mock_response
        self.assertEqual(mock_response, Request.get(''))


class RequestGetJsonTest(unittest.TestCase):
    def setUp(self):
        patcher = patch('taktyk.request.Request.get')
        self.mock_request_get = patcher.start()
        self.addCleanup(patcher.stop)

    def test_if_kwargs_are_passed_to_request_get(self):
        url = 'http://url.com'
        kwargs = {'exit_': False, 'msg': 'test', 'timeout': 21, 'stream': True}
        Request.get_json(url, **kwargs)
        self.mock_request_get.assert_called_with(url, **kwargs)

    def test_when_response_ok_and_json_is_dict_with_error_or_empty(self):
        mock_response = Mock()
        mock_response.json.side_effect = [{'error': 'error135'}, {}]
        self.mock_request_get.return_value = mock_response
        with self.assertRaises(ValueError) as ex:
            Request.get_json('')
        ex_msg = str(ex.exception)
        self.assertEqual(ex_msg, 'error135')
        with self.assertRaises(ValueError) as ex:
            Request.get_json('')
        ex_msg = str(ex.exception)
        self.assertEqual(ex_msg, 'None')

    def test_when_response_ok_and_json_is_list_and_empty(self):
        mock_response = Mock()
        mock_response.json.return_value = []
        self.mock_request_get.return_value = mock_response
        with self.assertRaises(ValueError) as ex:
            Request.get_json('')
        ex_msg = str(ex.exception)
        self.assertEqual(ex_msg, 'Empty list')

    def test_when_response_ok_and_json_ok(self):
        mock_response = Mock()
        mock_response.json.side_effect = [{'id': 111}, ['not_empty']]
        self.mock_request_get.return_value = mock_response
        self.assertEqual({'id': 111}, Request.get_json(''))
        self.assertEqual(['not_empty'], Request.get_json(''))

    @patch('logging.error')
    def test_when_exception_raised_and_msg_passed(self, mock_log_err):
        self.mock_request_get.return_value = None
        with self.assertRaises(ValueError):
            Request.get_json('', msg='error msg')
        mock_log_err.assert_called_with('error msg')

    def test_when_exception_raised_and_exit_true(self):
        self.mock_request_get.return_value = []
        with self.assertRaises(SystemExit):
            Request.get_json('', exit_=True)
