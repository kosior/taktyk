import os
import shutil
import sys
import sqlite3
import unittest
from unittest.mock import patch, Mock

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.entry import Entry
from taktyk.db import DB, database_list, set_added_info
from taktyk import settings


class Prepare(unittest.TestCase):
    def setUp(self):
        settings.ENTRIES_ADDED = 0
        settings.COMMENTS_ADDED = 0
        settings.USER_FILES_PATH = os.path.join(settings.SAVE_PATH, 'tests')
        self.path = os.path.join(settings.USER_FILES_PATH, 'db')
        os.makedirs(self.path, exist_ok=True)
        self.entry = Entry(id_=1, author='test_author', date='test_date', body='test_body',
                           body_html='test_body_html', url='test_url', plus='1000',
                           media_url='test_media_url', tags=' testtag1 ', is_nsfw=False,
                           entry_id=None, type_='entry')

    def tearDown(self):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path)


class DBCreationTest(Prepare):
    def test_create_new_without_name(self):
        DB.create_new('')
        self.assertTrue(os.path.isfile(os.path.join(self.path, settings.DB_NAME)))

    def test_create_new_with_name(self):
        DB.create_new('test')
        self.assertTrue(os.path.isfile(os.path.join(self.path, 'test.db')))

    @patch('taktyk.db.Decision')
    def test_ask_and_create_without_name(self, mock_decision):
        dec_ins = Mock()
        dec_ins.run.return_value = ''
        mock_decision.return_value = dec_ins
        DB.ask_and_create()
        self.assertTrue(os.path.isfile(os.path.join(self.path, settings.DB_NAME)))
        self.assertTrue(dec_ins.run.called)

    @patch('taktyk.db.Decision')
    def test_ask_and_create_with_name(self, mock_decision):
        dec_ins = Mock()
        dec_ins.run.return_value = 'test_name'.strip()
        mock_decision.return_value = dec_ins
        DB.ask_and_create()
        self.assertTrue(os.path.isfile(os.path.join(self.path, 'test_name.db')))
        self.assertTrue(dec_ins.run.called)

    def test_if_tables_are_correct(self):
        DB.create_new('test')
        connection = sqlite3.connect(os.path.join(self.path, 'test.db'))
        connection.execute('SELECT * FROM entry')
        connection.execute('SELECT * FROM entry_comment')


class InsertOneTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')
        self.db_path = os.path.join(self.path, 'test.db')
        self.entry = Entry(id_=123, author='test_author', date='test_date', body='test_body',
                           body_html='test_body_html', url='test_url', plus='1000',
                           media_url='test_media_url', tags=' testtag1 testtag2 ', is_nsfw=False,
                           entry_id=None, type_='entry')

    def test_when_object_passed_is_none(self):
        with DB.Connect() as cursor:
            self.assertFalse(DB.insert_one(cursor, []))

    def test_when_entry_passed(self):
        with DB.Connect() as cursor:
            self.assertTrue(DB.insert_one(cursor, self.entry))
            db_entry = cursor.execute('SELECT * FROM entry').fetchone()
            self.assertEqual(db_entry, tuple(self.entry))
            self.assertEqual(1, settings.ENTRIES_ADDED)

    def test_when_entry_comment_passed(self):
        self.entry.type_ = 'entry_comment'
        self.entry.entry_id = 321
        with DB.Connect() as cursor:
            self.assertTrue(DB.insert_one(cursor, self.entry))
            db_entry = cursor.execute('SELECT * FROM entry_comment').fetchone()
            self.assertEqual(db_entry, tuple(self.entry))
            self.assertEqual(1, settings.COMMENTS_ADDED)

    def test_when_try_add_entry_already_in_db(self):
        with DB.Connect() as cursor:
            self.assertTrue(DB.insert_one(cursor, self.entry))
            self.assertFalse(DB.insert_one(cursor, self.entry))


class GetIdsTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')

    def test_if_ids_correctly_returned_from_entry(self):
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 3
            DB.insert_one(cursor, self.entry)
            self.assertEqual({1, 2, 3}, set(DB.get_ids(cursor, 'entry')))

    def test_if_ids_correctly_returned_from_entry_comment(self):
        self.entry.type_ = 'entry_comment'
        self.entry.entry_id = 321
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 3
            DB.insert_one(cursor, self.entry)
            self.assertEqual({1, 2, 3}, set(DB.get_ids(cursor, 'entry_comment')))

    def test_if_ids_returned_if_tag_is_matched(self):
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 3
            self.entry.tags = ' testtag2 '
            DB.insert_one(cursor, self.entry)
            self.assertEqual({1, 2}, set(DB.get_ids(cursor, 'entry', tag='testtag1')))

    def test_if_ids_if_nsfw_filtering_on(self):
        settings.NSFW_FILTER = True
        with DB.Connect() as cursor:
            self.entry.is_nsfw = True
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            self.entry.is_nsfw = True
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 3
            self.entry.is_nsfw = False
            DB.insert_one(cursor, self.entry)
            self.assertEqual({3}, set(DB.get_ids(cursor, 'entry')))

    def test_if_decorator_works_when_cursor_not_passed(self):
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            DB.insert_one(cursor, self.entry)
        self.assertEqual({1, 2}, set(DB.get_ids('entry')))

    def test_if_date_sorting_works(self):
        with DB.Connect() as cursor:
            self.entry.date = '5.06.2017'
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            self.entry.date = '7.06.2017'
            DB.insert_one(cursor, self.entry)
            self.assertEqual([2, 1], list(DB.get_ids('entry')))


class GetEntryRowTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')

    def test_if_row_returned(self):
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            row = DB.get_entry_row(cursor, 1)
        self.assertEqual(row, tuple(self.entry))

    def test_when_id_not_in_db(self):
        with DB.Connect() as cursor:
            row = DB.get_entry_row(cursor, 2)
        self.assertIsNone(row)

    def test_when_cursor_not_passed(self):
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
        row = DB.get_entry_row(1)
        self.assertEqual(row, tuple(self.entry))


class GetCommentsByEntryIdTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')

    def test_if_comments_returned(self):
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 1
            self.entry.entry_id = 1
            self.entry.type_ = 'entry_comment'
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            self.entry.entry_id = 1
            self.entry.type_ = 'entry_comment'
            DB.insert_one(cursor, self.entry)
            result = list(DB.get_comments_by_entry_id(cursor, 1))
            self.assertEqual(2, len(result))
        result = list(DB.get_comments_by_entry_id(1))  # called without cursor passed
        self.assertEqual(2, len(result))

    def test_if_comments_not_found(self):
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            result = list(DB.get_comments_by_entry_id(cursor, 1))
            self.assertEqual([], result)


class GetEntryWithCommentsTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')

    def test_if_entry_with_comments_returned(self):
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 1
            self.entry.entry_id = 1
            self.entry.type_ = 'entry_comment'
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            self.entry.entry_id = 1
            self.entry.type_ = 'entry_comment'
            DB.insert_one(cursor, self.entry)
            entry = DB.get_entry_with_comments(cursor, 1)
            self.assertEqual(1, entry.id_)
            self.assertEqual(2, len(list(entry.comments)))
        entry = DB.get_entry_with_comments(1)
        self.assertEqual(1, entry.id_)
        self.assertEqual(2, len(list(entry.comments)))


class GetAllEntriesWithCommentsTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            self.entry.tags = ' testtag2 '
            DB.insert_one(cursor, self.entry)
            for e_id in (1, 2):
                for i in range(1, 4):
                    self.entry.id_ = i + e_id * 4  # fix for different ids
                    self.entry.entry_id = e_id
                    self.entry.type_ = 'entry_comment'
                    DB.insert_one(cursor, self.entry)

    def test_if_return_is_correct(self):
        with DB.Connect() as cursor:
            result = list(DB.get_all_entries_with_comments(cursor))
            self.assertEqual(2, len(result))
            for entry in result:
                self.assertEqual(3, len(list(entry.comments)))

    def test_if_tag_filter_works(self):
        with DB.Connect() as cursor:
            result = list(DB.get_all_entries_with_comments(cursor, tag='testtag2'))
            self.assertEqual(1, len(result))


class CountTagsTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 3
            self.entry.tags = ' differenttag '
            DB.insert_one(cursor, self.entry)

    def test_if_result_correct(self):
        tags = DB.count_tags()
        self.assertTrue(('testtag1', 2) in tags)
        self.assertTrue(('differenttag', 1) in tags)

    def test_if_tag_filter_works(self):
        tags = DB.count_tags(arg_tag='differenttag')
        self.assertEqual(1, len(tags))


class DeleteEntryTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            self.entry.entry_id = 1
            self.entry.type_ = 'entry_comment'
            DB.insert_one(cursor, self.entry)

    def test_if_everything_is_deleted(self):
        with DB.Connect() as cursor:
            DB.delete_entry(cursor, 1)
            e_ids = DB.get_ids(cursor, 'entry')
            c_ids = DB.get_ids(cursor, 'entry_comment')
        self.assertEqual(0, len(e_ids))
        self.assertEqual(0, len(c_ids))


class CountCommentsTest(Prepare):
    def setUp(self):
        super().setUp()
        DB.create_new('test')
        with DB.Connect() as cursor:
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 2
            self.entry.entry_id = 1
            self.entry.type_ = 'entry_comment'
            DB.insert_one(cursor, self.entry)
            self.entry.id_ = 3
            self.entry.entry_id = 1
            self.entry.type_ = 'entry_comment'
            DB.insert_one(cursor, self.entry)

    def test_if_correct_result(self):
        self.assertEqual(2, DB.count_comments(entry_id=1))


class DatabaseListTest(Prepare):
    def test_if_result_correct(self):
        DB.create_new('test1')
        DB.create_new('test2')
        result = database_list(self.path)
        self.assertTrue('test1.db' in result)
        self.assertTrue('test2.db' in result)


class SetAddedInfoTest(unittest.TestCase):
    def setUp(self):
        settings.ENTRIES_ADDED = 0
        settings.COMMENTS_ADDED = 0

    def test_when_entry_added(self):
        set_added_info('entry')
        self.assertEqual(1, settings.ENTRIES_ADDED)

    def test_when_comment_added(self):
        set_added_info('entry_comment')
        set_added_info('entry_comment')
        self.assertEqual(2, settings.COMMENTS_ADDED)
