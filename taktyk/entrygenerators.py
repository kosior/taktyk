import abc

from . import settings
from .db import DB
from .parsers import JsonParser, HtmlParser


class GenerateStrategy(metaclass=abc.ABCMeta):
    def __init__(self, parser_cls, db_handler=None):
        self.parser_cls = parser_cls
        self.db_handler = db_handler or DB
        self.full_update = settings.FULL_UPDATE
        self.db_ids = settings.DB_IDS
        self.nsfw_filter = settings.NSFW_FILTER

    @abc.abstractmethod
    def generate(self, raw_source):
        """Method will generate entry/entries from raw_source using parser passed in __init__"""
        pass


class APIMethod(GenerateStrategy):
    """Strategy for generating Entry objects using WykopAPI"""
    def __init__(self, parser_cls=None, db_handler=None):
        super().__init__(parser_cls=parser_cls or JsonParser, db_handler=db_handler)

    def generate(self, raw_source):
        if isinstance(raw_source, list):
            return self.gen_many_entries(raw_source)
        elif isinstance(raw_source, dict):
            return self.gen_one_entry(raw_source)

    def gen_one_entry(self, json_, db_comment_count=None):
        parser = self.parser_cls(json_)
        entry = parser.entry

        if not entry.id_:
            raise StopIteration('Entry is empty')

        if entry.id_ not in self.db_ids:
            parser.parse()
            if self.nsfw_filter and entry.is_nsfw:
                raise StopIteration('Unwanted nsfw content.')
            yield entry
        elif self.full_update:
            db_comment_count = db_comment_count or self.db_handler.count_comments(entry.id_)
        else:
            raise StopIteration('Entry already in database.')

        comments = json_.get('comments')
        comments = comments[db_comment_count:]  # slicing list for new comments only

        for comment in comments:
            yield self.parser_cls(comment).parse()

    def gen_many_entries(self, raw_entries_list):
        for raw_json in raw_entries_list:
            for entry in self.gen_one_entry(raw_json):
                yield entry


class ScrapeMethod(GenerateStrategy):
    """Strategy for generating Entry objects using BeautifulSop"""
    def __init__(self, parser_cls=None, db_handler=None):
        super().__init__(parser_cls=parser_cls or HtmlParser, db_handler=db_handler)

    def generate(self, raw_source):
        """raw_source - (id_, soup)"""
        return self.gen_one_entry(*raw_source)

    def gen_one_entry(self, id_, raw_entry):
        comments_start_index = 1  # start from 1 because 0 = main entry
        parser = self.parser_cls(id_, raw_entry)

        if int(id_) not in self.db_ids:
            main_entry = parser.get_main_entry()
            if (not main_entry) or (self.nsfw_filter and main_entry.is_nsfw):
                raise StopIteration('Entry is empty or unwanted nsfw content.')
            yield main_entry
        elif self.full_update:
            comments_start_index += self.db_handler.count_comments(id_)  # index for new comments
        else:
            raise StopIteration('Entry already in database.')

        for comment in parser.get_comments_generator(comments_start_index):
            if comment:
                yield comment
