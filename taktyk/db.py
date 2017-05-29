import logging
import os
import sqlite3
import time
import traceback
from contextlib import ContextDecorator

from . import settings
from .entry import Entry


class DB:
    connection = None
    cursor = None

    @classmethod
    def create_new(cls, name):
        if name:
            settings.DB_NAME = name + '.db'
        else:
            settings.DB_NAME = 'taktyk-{}.db'.format(time.strftime('%Y%m%d%H%M%S'))
        cls.create()

    class Connect(ContextDecorator):
        def __enter__(self):
            full_db_path = os.path.join(settings.USER_FILES_PATH,
                                        settings.DB_DIR_NAME,
                                        settings.DB_NAME)
            self.conn = sqlite3.connect(full_db_path)
            self.cursor = self.conn.cursor()
            DB.connection = self.conn
            DB.cursor = self.cursor
            return self.cursor

        def __exit__(self, *exc):
            self.conn.commit()
            self.conn.close()
            DB.connection = None
            DB.cursor = None

        def __call__(self, func):
            def wrapper(*args, **kwargs):
                index = 0
                args = list(args)
                for arg in args[:2]:
                    if arg == DB or isinstance(arg, DB):
                        index = 1
                    elif isinstance(arg, sqlite3.Cursor):
                        if arg.connection == DB.connection:
                            return func(*args, **kwargs)
                        else:
                            args.pop(index)
                            break
                    else:
                        break

                if DB.connection:
                    args.insert(index, DB.cursor)
                    return func(*args, **kwargs)
                else:
                    with self as cur:
                        args.insert(index, cur)
                        return func(*args, **kwargs)
            return wrapper

    connect = Connect

    @staticmethod
    @connect()
    def create(cursor):
        try:
            cursor.execute('''CREATE TABLE entry (
                                id INTEGER(20) NOT NULL PRIMARY KEY,
                                author VARCHAR(80) NOT NULL,
                                date VARCHAR(20) NOT NULL,
                                body LONGTEXT,
                                body_html LONGTEXT,
                                url VARCHAR(40) NOT NULL,
                                plus VARCHAR(5) NOT NULL,
                                media_url VARCHAR(255),
                                tags VARCHAR(255),
                                is_nsfw BOOLEAN NOT NULL,
                                entry_id INTEGER(20)
                                )''')

            cursor.execute('''CREATE TABLE entry_comment (
                                id INTEGER(20) NOT NULL PRIMARY KEY,
                                author VARCHAR(80) NOT NULL,
                                date VARCHAR(20) NOT NULL,
                                body LONGTEXT,
                                body_html LONGTEXT,
                                url VARCHAR(40) NOT NULL,
                                plus VARCHAR(5) NOT NULL,
                                media_url VARCHAR(255),
                                tags VARCHAR(255),
                                is_nsfw BOOLEAN NOT NULL,
                                entry_id INTEGER(20) NOT NULL,
                                FOREIGN KEY (entry_id) REFERENCES entry (id) ON DELETE CASCADE
                                )''')
        except sqlite3.OperationalError:
            logging.debug(traceback.format_exc())

    @staticmethod
    def insert_one(cursor, obj):
        """Insert entry or comment into database"""
        if not obj:
            logging.debug('Entry is empty.')
            return False

        statement = 'INSERT INTO {} VALUES (?,?,?,?,?,?,?,?,?,?,?)'.format(obj.type_)
        params = tuple(obj.__iter__())

        try:
            cursor.execute(statement, params)
        except sqlite3.IntegrityError:
            logging.info(traceback.format_exc())
        else:
            set_added_info(obj.type_)
            return True

    @classmethod
    @connect()
    def get_ids(cls, cursor, table: '"entry" or "entry_comment"', tag=None):
        condition, params = cls.get_condition_and_params(tag)
        statement = 'SELECT id FROM {} {} ORDER BY date DESC'.format(table, condition)
        try:
            return [row[0] for row in cursor.execute(statement, params).fetchall()]
        except sqlite3.IntegrityError:
            logging.debug('Fetching ids failed')

    @staticmethod
    @connect()
    def get_entry_row(cursor, id_):
        statement = 'SELECT * FROM entry WHERE id = (?)'
        params = (id_,)
        try:
            row = cursor.execute(statement, params).fetchone()
        except sqlite3.IntegrityError:
            logging.debug('Fetching entry failed')
        else:
            return row

    @staticmethod
    @connect()
    def get_comments_by_entry_id(cursor, id_):
        statement = 'SELECT * FROM entry_comment WHERE entry_id = (?)'
        params = (id_,)
        try:
            return (Entry(*row) for row in cursor.execute(statement, params).fetchall())
        except sqlite3.IntegrityError:
            logging.debug('Fetching comments for entry failed')
        except TypeError:
            logging.debug(traceback.format_exc())

    @classmethod
    @connect()
    def get_entry_with_comments(cls, cursor, id_):
        row = cls.get_entry_row(cursor, id_)
        try:
            entry = Entry(*row)
        except TypeError:
            logging.debug(traceback.format_exc())
        else:
            entry.comments = cls.get_comments_by_entry_id(cursor, id_)
            return entry

    @classmethod
    @connect()
    def get_all_entries_with_comments(cls, cursor, tag=None):
        return (cls.get_entry_with_comments(id_) for id_ in cls.get_ids(cursor, 'entry', tag=tag))

    @classmethod
    @connect()
    def count_tags(cls, cursor, arg_tag=None):
        tags_dict = {}
        condition, params = cls.get_condition_and_params(arg_tag)
        statement = 'SELECT tags FROM entry {}'.format(condition)
        try:
            tags = cursor.execute(statement, params).fetchall()
        except sqlite3.IntegrityError:
            logging.debug('Fetching tags failed')
            return

        for tags_row in tags:
            tags = set(tags_row[0].split(' '))
            for tag in tags:
                if tag in tags_dict.keys():
                    tags_dict[tag] += 1
                else:
                    tags_dict[tag] = 1

        return sorted(tags_dict.items(), key=lambda x: x[1], reverse=True)

    @staticmethod
    @connect()
    def delete_entry(cursor, entry_id):
        try:
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.execute('DELETE FROM entry WHERE id=(?)', (entry_id,))
        except sqlite3.IntegrityError:
            logging.debug('Deletion failed: %s', entry_id)
            return False

    @staticmethod
    @connect()
    def count_comments(cursor, entry_id):
        statement = 'SELECT id FROM entry_comment WHERE entry_id=(?)'
        params = (entry_id,)
        try:
            comments_ids = cursor.execute(statement, params).fetchall()
        except sqlite3.IntegrityError:
            logging.debug(traceback.format_exc())
        else:
            return len(comments_ids)

    @staticmethod
    def get_condition_and_params(tag):
        condition = ''
        params = {}
        if settings.NSFW_FILTER:
            params['nsfw'] = 0
            condition = 'WHERE is_nsfw = :nsfw'
        if tag:
            params['tag'] = '% {} %'.format(tag)
            tag_condition = 'tags LIKE :tag'
            if condition:
                condition += ' AND {}'.format(tag_condition)
            else:
                condition = 'WHERE {}'.format(tag_condition)
        return condition, params


def database_list(path):
    return [file for file in os.listdir(path) if file.endswith('.db')]


def set_added_info(type_):
    if type_ == 'entry':
        settings.ENTRIES_ADDED += 1
    elif type_ == 'entry_comment':
        settings.COMMENTS_ADDED += 1
