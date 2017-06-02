import os
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.contentdelivery import HtmlContent, ApiContent, gen_entries_by_ids_with_futures


class GenEntriesByIdsWithFuturesTest(unittest.TestCase):
    def test_if_return_values_are_correct(self):
        def test_func(url_, id_): return url_ + id_
        ids = ['1', '2', '3', '4']
        url = 'someurl'
        test_gen = gen_entries_by_ids_with_futures(test_func, url, ids=ids, max_workers=3)
        result_expected = {url + id_ for id_ in ids}
        result = set(test_gen)
        self.assertEqual(result_expected, result)

    def test_if_only_true_values_are_returned(self):
        ids = ['1', '2', '3', '4']
        test_func = Mock(side_effect=['', 1, '2', []])
        test_gen = gen_entries_by_ids_with_futures(test_func, ids=ids, max_workers=3)
        self.assertEqual(len(list(test_gen)), 2)


class ApiContentTest(unittest.TestCase):
    def setUp(self):
        self.content = ApiContent(appkey='appkey123', userkey='userkey123', secret='secret123')
        patcher = patch('taktyk.request.Request.get_json', return_value={'json': 'content'})
        patcher2 = patch('taktyk.contentdelivery.apisign', return_value='md5')
        self.addCleanup(patcher.stop)
        self.addCleanup(patcher2.stop)
        self.mock_get_json = patcher.start()
        self.mock_apisign = patcher2.start()

    def test_init_urls(self):
        self.assertIn('userkey123', self.content.fav_url)
        self.assertIn('appkey123', self.content.fav_url)
        self.assertIn('appkey123', self.content.entry_url)

    def test_get_json_if_correct_urls_are_passed_to_requester_when_fav_url(self):
        self.content.fav_url = 'fav_url'
        self.content.entry_url = 'entry_url'
        self.content.page_num = 36
        self.content.get_json(self.content.fav_url)
        self.mock_get_json.assert_called_with('fav_url36', exit_=False, headers='md5')

    def test_get_json_if_correct_urls_are_passed_to_requester_when_entry_url(self):
        self.content.entry_url = 'entry_url{index}'
        id_ = 25
        self.content.get_json(self.content.entry_url, id_=id_)
        self.mock_get_json.assert_called_with('entry_url25', exit_=False, headers='md5')

    def test_get_json_for_valuerror_when_no_url_matched_or_no_id(self):
        with self.assertRaises(ValueError):
            self.content.get_json('wrong_url')
        with self.assertRaises(ValueError):
            self.content.get_json(self.content.entry_url)

    def test_get_json_when_valueerror_raised_from_requester(self):
        self.mock_get_json.side_effect = ValueError
        self.assertEqual([], self.content.get_json(self.content.fav_url))

    def test_get_json_if_correct_value_is_returned(self):
        self.mock_get_json.return_value = 'somejson'
        self.assertEqual('somejson', self.content.get_json(self.content.fav_url))

    def test_submit_to_executor_when_page_is_not_none(self):
        mock_executor = Mock()
        mock_submit = Mock(return_value='future')
        mock_executor.submit = mock_submit
        self.assertEqual('future', self.content.submit_to_executor(mock_executor))
        mock_submit.assert_called_with(self.content.get_json, self.content.fav_url)
        self.assertEqual(1, self.content.page_num)  # checking if page_num_incremented

    def test_submit_to_executor_when_page_is_none(self):
        self.content.page_num = None
        self.assertFalse(self.content.submit_to_executor(Mock()))

    def test_gen_entries_if_correct_incrementing_and_output(self):
        return_lst = ['resul1', 'result2', 'result3', []]
        self.mock_get_json.side_effect = return_lst
        self.assertEqual(return_lst[:3], list(self.content.gen_entries()))

    def test_gen_entries_with_ids_if_correct_output(self):
        return_lst = ['resul1', 'result2', 'result3', [], 'result5']
        expected_result = {'resul1', 'result2', 'result3', 'result5'}
        ids = [1, 2, 3, 4, 5]
        self.mock_get_json.side_effect = return_lst
        self.assertEqual(expected_result, set(self.content.gen_entries_by_ids(ids)))


class HtmlContentTest(unittest.TestCase):
    def setUp(self):
        self.content = HtmlContent()
        self.content.entry_url = 'entry_url'
        mock_response = Mock()
        mock_response.text = '<html></html>'
        patcher = patch('taktyk.request.Request.get', return_value=mock_response)
        self.mock_get = patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_entry_check_call(self):
        self.content.get_entry('123')
        self.mock_get.assert_called_with('entry_url123', exit_=False)

    def test_get_entry_response_ok(self):
        self.assertEqual(self.content.get_entry('123'), ('123', '<html></html>'))

    def test_get_entry_response_not_200(self):
        self.mock_get.return_value = Mock(spec=[])
        self.assertEqual([], self.content.get_entry('abcd'))

    def test_gen_html_entries_by_ids_if_correct_len(self):
        ids = ['1', '2', '3', '4']
        lst = list(self.content.gen_html_entries_by_ids(ids))
        self.assertEqual(len(lst), 4)

    def test_gen_html_entries_by_ids_if_correct_output(self):
        ids = ['1', '2']
        result = list(self.content.gen_html_entries_by_ids(ids))
        self.assertTrue(('1', '<html></html>') in result)
        self.assertTrue(('2', '<html></html>') in result)

    def test_gen_html_entries_by_ids_if_request_failed(self):
        ids = ['1', '2']
        self.mock_get.return_value = Mock(spec=[])
        lst = list(self.content.gen_html_entries_by_ids(ids))
        self.assertEqual(len(lst), 0)
