import os
import sys
import unittest
from unittest.mock import Mock

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.entry import Entry
from taktyk.entrygenerators import APIMethod, ScrapeMethod


class ApiMethodTest(unittest.TestCase):
    def setUp(self):
        class FakeParser:
            def __init__(self, json_):
                self.id_ = json_.get('id_')
                self.mock_entry = Mock()
                self.mock_entry.id_ = self.id_
                self.mock_entry.is_nsfw = json_.get('is_nsfw')
                self.entry = self.mock_entry

            def parse(self):
                entry = 'entry{}'.format(self.id_)
                self.entry.id_ = entry
                return self.entry

        self.parser_cls = FakeParser
        self.db = Mock()
        self.api = APIMethod(self.parser_cls, self.db)

    def test_wut(self):
        parser = self.parser_cls({})
        entry = parser.entry
        print(parser.parse())
        print(entry)

    def test_args(self):
        self.assertTrue(self.api.parser_cls, self.parser_cls)
        self.assertTrue(self.api.db_handler, self.db)

    def test_generate(self):
        self.api.gen_one_entry = Mock(return_value='one_entry')
        self.api.gen_many_entries = Mock(return_value='many_entries')
        self.assertEqual(self.api.generate({}), 'one_entry')
        self.assertEqual(self.api.generate([]), 'many_entries')

    def test_gen_many_entries(self):
        self.api.gen_one_entry = Mock(return_value=(x for x in range(3)))
        raw_entries_list = [{}, {}, {}]
        count = 0
        for entry in self.api.gen_many_entries(raw_entries_list):
            self.assertEqual(entry, count)
            count += 1

    def test_gen_one_entry_when_no_entry_id(self):
        with self.assertRaises(StopIteration):
            next(self.api.gen_one_entry({}))

    def test_gen_one_entry_when_id_in_db_and_full_update_false(self):
        self.api.full_update = False
        self.api.db_ids = [1]
        with self.assertRaises(StopIteration):
            next(self.api.gen_one_entry({'id_': 1}))

    def test_gen_one_entry_when_id_not_in_db_but_nsfw_filter_on(self):
        self.api.nsfw_filter = True
        with self.assertRaises(StopIteration):
            next(self.api.gen_one_entry({'id_': 1, 'is_nsfw': True}))

    def test_gen_one_entry_when_id_not_in_db_and_nsfw_filter_off(self):
        self.api.nsfw_filter = False
        entry = next(self.api.gen_one_entry({'id_': 1, 'is_nsfw': True}))
        self.assertEqual('entry1', entry.id_)

    def test_gen_one_entry_when_id_not_in_db_and_nsfw_filter_on_but_entry_is_nsfw_false(self):
        self.api.nsfw_filter = True
        entry = next(self.api.gen_one_entry({'id_': 2, 'is_nsfw': False}))
        self.assertEqual('entry2', entry.id_)

    def test_if_comments_returned(self):
        comments = [{'id_': 'com1'}, {'id_': 'com2'}, {'id_': 'com3'}]
        json_ = {'id_': 25, 'comments': comments}
        expected_result = ['entry25', 'entrycom1', 'entrycom2', 'entrycom3']
        result = [entry.id_ for entry in list(self.api.gen_one_entry(json_))]
        self.assertEqual(expected_result, result)

    def test_when_entry_id_in_db_and_if_comments_are_filtered(self):
        comments = [{'id_': 'old1'}, {'id_': 'old2'}, {'id_': 'old3'}, {'id_': 'new4'},
                    {'id_': 'new5'}]
        json_ = {'id_': 1, 'comments': comments}
        self.api.full_update = True
        self.api.db_ids = [1]
        self.api.db_handler.count_comments.return_value = 3
        expected_result = ['entrynew4', 'entrynew5']
        result = [entry.id_ for entry in list(self.api.gen_one_entry(json_))]
        self.assertEqual(expected_result, result)


class ApiMethodGenOneEntryTest(unittest.TestCase):
    def setUp(self):
        entry = Entry(id_=123)
        self.parser = Mock()
        self.parser.parse.return_value = entry
        self.parser.entry = entry
        self.parser_cls = Mock(return_value=self.parser)
        self.db = Mock()
        self.api = APIMethod(self.parser_cls, self.db)

    def test_entry_id_not_in_db_ids_and_nsfw_consistent(self):
        self.api.db_ids = []
        self.api.nsfw_filter = True
        self.parser.entry.is_nsfw = True
        with self.assertRaises(StopIteration):
            next(self.api.gen_one_entry({}))

    def test_entry_id_not_in_db_ids_and_nsfw_inconsistent(self):
        self.api.db_ids = []
        self.api.nsfw_filter = False
        self.parser.entry.is_nsfw = True
        self.assertEqual(next(self.api.gen_one_entry({})), self.parser.entry)
        self.api.nsfw_filter = True
        self.parser.entry.is_nsfw = False
        self.assertEqual(next(self.api.gen_one_entry({})), self.parser.entry)
        self.api.nsfw_filter = False
        self.parser.entry.is_nsfw = False
        self.assertEqual(next(self.api.gen_one_entry({})), self.parser.entry)

    def test_entry_id_in_db_ids_and_full_update_false(self):
        self.api.full_update = False
        self.api.db_ids = [123]
        with self.assertRaises(StopIteration):
            next(self.api.gen_one_entry({}))

    def test_entry_id_not_in_db_ids_checking_comments(self):
        self.api.db_ids = []
        self.api.nsfw_filter = False
        comments = [{}, {}, {}]
        json_ = {'comments': comments}
        gen = self.api.gen_one_entry(json_)
        for entry in gen:
            self.assertEqual(entry, self.parser.entry)
        lst = list(self.api.gen_one_entry(json_))
        self.assertEqual(len(lst), 4)

    def test_entry_id_in_db_ids_and_full_update_true(self):
        self.api.full_update = True
        self.api.nsfw_filter = False
        self.api.db_ids = [123]
        comments = [{}, {}, {}]
        json_ = {'comments': comments}
        lst = list(self.api.gen_one_entry(json_, db_comment_count=2))
        self.assertEqual(len(lst), 1)


class ScrapeMethodTest(unittest.TestCase):
    def setUp(self):
        self.parser = Mock()
        self.db = Mock()
        self.scrape = ScrapeMethod(self.parser, self.db)

    def test_args(self):
        self.assertTrue(self.scrape.parser_cls, self.parser)
        self.assertTrue(self.scrape.db_handler, self.db)

    def test_generate(self):
        self.scrape.gen_one_entry = Mock(return_value='one_entry')
        self.assertEqual(self.scrape.generate(('id', 'html')), 'one_entry')


class ScrapeMethodGenOneEntryTest(unittest.TestCase):
    def setUp(self):
        self.parser = Mock()
        self.parser.get_main_entry.return_value = Entry(id_='123')
        self.parser_cls = Mock(return_value=self.parser)
        self.db_handler = Mock()
        self.scrape = ScrapeMethod(self.parser_cls, self.db_handler)

    def test_id_not_in_db_ids_and_nsfw_is_consistent(self):
        self.scrape.db_ids = []
        self.scrape.nsfw_filter = True
        self.parser.get_main_entry.return_value = Entry(is_nsfw=True)
        with self.assertRaises(StopIteration):
            next(self.scrape.gen_one_entry('47', 'html'))

    def test_id_not_in_db_ids_nsfw_not_consistent(self):
        self.scrape.db_ids = [123]
        self.scrape.nsfw_filter = True
        entry = Entry(is_nsfw=False)
        self.parser.get_main_entry.return_value = entry
        self.assertEqual(next(self.scrape.gen_one_entry('1', 'html')), entry)

    def test_id_in_db_ids_full_update_false(self):
        self.scrape.db_ids = [123]
        self.scrape.full_update = False
        self.parser.get_main_entry.return_value = Entry()
        with self.assertRaises(StopIteration):
            next(self.scrape.gen_one_entry('123', 'html'))

    def test_if_comments_are_yielded(self):
        self.scrape.db_ids = []
        self.scrape.nsfw_filter = False
        entry = Entry(id_='22')
        comment = Entry(id_='44')
        self.parser.get_main_entry.return_value = entry
        self.parser.get_comments_generator.return_value = (c for c in [comment, comment, comment])
        gen = self.scrape.gen_one_entry('22', 'html')
        self.assertEqual(next(gen).id_, entry.id_)
        self.assertEqual(next(gen).id_, comment.id_)
        self.assertEqual(next(gen).id_, comment.id_)
        self.assertEqual(next(gen).id_, comment.id_)
        with self.assertRaises(StopIteration):
            next(gen)

    def test_comments_start_index_id_in_db_ids(self):
        self.scrape.db_ids = [123]
        self.scrape.nsfw_filter = False
        self.scrape.full_update = True
        self.db_handler.count_comments.return_value = 3
        self.parser.get_comments_generator = Mock(return_value=['comment', 'comment', 'comment'])
        next(self.scrape.gen_one_entry('123', 'html'))
        self.parser.get_comments_generator.assert_called_with(4)
