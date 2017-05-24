import logging

from .abs_base import AbsCommand
from .validators import userkey_validator, source_validator, ids_validator
from .. import auth, settings
from ..db import DB
from ..entrygenerators import ScrapeMethod
from ..render import HtmlFile
from ..request import Request
from ..save import Multi, save_wrapper
from ..strategies import SourceStrategy, SessionStrategy, APIStrategy, SeleniumStrategy
from ..utils import Decision


class NewCommand(AbsCommand):
    name = 'new'

    def execute(self, *args):
        msg = 'Podaj nazwę dla bazy danych (0 - aby wyjść): '
        name = Decision(msg, {'0': exit}, validator=lambda x: x).run()
        DB.create_new(name.strip())
        logging.info('...utworzono nową bazę danych: ' + settings.DB_NAME)


class PdkCommand(AbsCommand):
    name = 'pdk'

    def execute(self, *args):
        msg = 'Podaj klucz użytkownika (0 - aby wyjść): '
        decision = Decision(msg, {'0': exit}, validator=userkey_validator)
        settings.USERKEY = decision.run()


class FileSourceCommand(AbsCommand):
    name = 'file'

    def execute(self, *args):
        msg = 'Podaj scieżkę do pliku lub folderu (0 - aby wyjść): '
        decision = Decision(msg, {'0': exit}, validator=source_validator)
        settings.SOURCE = decision.run()
        settings.STRATEGY = SourceStrategy


class SeleniumCommand(AbsCommand):
    name = 'selenium'

    def execute(self, arg, *args):
        settings.STRATEGY = SeleniumStrategy
        settings.BROWSER = arg


class SessionCommand(AbsCommand):
    name = 'session'

    def execute(self, *args):
        settings.STRATEGY = SessionStrategy


class DeleteCommand(AbsCommand):
    name = 'delete'

    def execute(self, arg, *args):
        msg = 'Wprowadz numery id wpisów do usunięcia: (0 - aby wyjść): '
        ids_del = Decision(msg, {'0': exit}, validator=ids_validator).run()

        db_choice = 'z bazy danych'
        wykop_choice = 'z ulubionych na stronie www.wykop.pl'
        all_choice = '{} oraz {}'.format(db_choice, wykop_choice)

        choice = {'db': db_choice, 'wykop': wykop_choice, 'all': all_choice}

        msg = 'Czy na pewno chcesz usunąć wprowadzone wpisy {} (T/n): '.format(choice.get(arg))

        Decision(msg, {'T': None, 'n': exit}).run()

        if arg in ['db', 'all']:
            logging.info('...kasowanie wpisów z bazy danych')
            self.delete_from_db(ids_del)
        if arg in ['wykop', 'all']:
            logging.info('...usuwanie wpisów z ulubionych na www.wykop.pl')
            self.delete_from_wykop(ids_del)
        exit()

    @staticmethod
    def delete_from_db(ids):
        with DB.connect() as cursor:
            for entry_id in ids:
                DB.delete_entry(cursor, entry_id)

    @staticmethod
    def delete_from_wykop(ids):
        auth.set_userkey()
        url = settings.API_UNFAV_URL_F.format(userkey=settings.USERKEY, appkey=settings.APPKEY)
        for id_ in ids:
            url = url.format(id=id_)
            try:
                Request.get_json(url, exit_=False, headers=auth.apisign(url, settings.SECRETKEY))
            except ValueError:
                logging.debug('Entry not deleted or not in favorites: ' + url)


class HtmlCommand(AbsCommand):
    name = 'html'

    def execute(self, *args):
        HtmlFile().create()
        exit()


class SaveCommand(AbsCommand):
    name = 'save'

    def execute(self, *args):
        logging.info('...pobieranie plików z bazy danych')
        db_entries = DB.get_all_entries_with_comments()
        multi = Multi(5, save_wrapper)
        with multi as mlt:
            for entry in db_entries:
                if entry.media_url:
                    mlt.put(entry.download_info())
                for comment in entry.comments:
                    if comment.media_url:
                        mlt.put(comment.download_info())
        exit()


class CommentsCommand(AbsCommand):
    name = 'comments'

    def execute(self, *args):
        logging.info('...aktualizacja komentarzy we wpisach')
        ids = DB.get_ids('entry')
        settings.FULL_UPDATE = True
        settings.SOURCE = {'ids': ids}
        settings.STRATEGY = SourceStrategy


class NsfwCommand(AbsCommand):
    name = 'nsfw'

    def execute(self, *args):
        settings.NSFW_FILTER = True


class SkipCommand(AbsCommand):
    name = 'skip'

    def execute(self, *args):
        settings.SKIP_FILES = True


class ScrapeCommand(AbsCommand):
    name = 'scrape'

    def execute(self, *args):
        settings.SCRAPE = True
        if settings.STRATEGY == APIStrategy:
            settings.STRATEGY = SessionStrategy
        settings.METHOD = ScrapeMethod


class IdsCommand(AbsCommand):
    name = 'ids'

    def execute(self, *args):
        msg = 'Wprowadz numery id: (0 - aby wyjść): '
        ids = Decision(msg, {'0': exit}, validator=ids_validator).run()
        settings.SOURCE = {'ids': ids}
        settings.STRATEGY = SourceStrategy
