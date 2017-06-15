import logging
import os
import shutil
import sys
import tempfile
from distutils.dir_util import copy_tree

from .abs_base import AbsCommand
from .validators import userkey_validator, source_validator, ids_validator
from .. import auth, settings
from ..db import DB
from ..entrygenerators import ScrapeMethod
from ..render import HtmlFile
from ..request import Request
from ..save import Multi, Save, save_wrapper
from ..strategies import SourceStrategy, SessionStrategy, APIStrategy, SeleniumStrategy
from ..utils import Decision, unpack_archive


class NewCommand(AbsCommand):
    name = 'new'

    def execute(self, *args):
        DB.ask_and_create()


class PdkCommand(AbsCommand):
    name = 'pdk'

    def execute(self, *args):
        msg = 'Podaj klucz użytkownika (0 - aby wyjść): '
        decision = Decision(msg, {'0': sys.exit}, validator=userkey_validator)
        settings.USERKEY = decision.run()


class FileSourceCommand(AbsCommand):
    name = 'file'

    def execute(self, *args):
        msg = 'Podaj scieżkę do pliku lub folderu (0 - aby wyjść): '
        decision = Decision(msg, {'0': sys.exit}, validator=source_validator)
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
        ids_del = self.get_ids()
        Decision(self.create_msg(arg), {'T': None, 'n': sys.exit}).run()

        if arg in ['db', 'all']:
            logging.info('...kasowanie wpisów z bazy danych')
            self.delete_from_db(ids_del)
        if arg in ['wykop', 'all']:
            logging.info('...usuwanie wpisów z ulubionych na www.wykop.pl')
            self.delete_from_wykop(ids_del)
        sys.exit()

    @staticmethod
    def get_ids():
        msg = 'Wprowadz numery id wpisów do usunięcia: (0 - aby wyjść): '
        ids_del = Decision(msg, {'0': sys.exit}, validator=ids_validator).run()
        return ids_del

    @staticmethod
    def create_msg(arg):
        db_choice = 'z bazy danych'
        wykop_choice = 'z ulubionych na stronie www.wykop.pl'
        all_choice = '{} oraz {}'.format(db_choice, wykop_choice)
        choice = {'db': db_choice, 'wykop': wykop_choice, 'all': all_choice}
        msg = 'Czy na pewno chcesz usunąć wprowadzone wpisy {} (T/n): '.format(choice.get(arg))
        return msg

    @staticmethod
    def delete_from_db(ids):
        with DB.connect() as cursor:
            for entry_id in ids:
                DB.delete_entry(cursor, entry_id)

    @staticmethod
    def delete_from_wykop(ids):
        auth.set_userkey()
        url_to_format = settings.API_UNFAV_URL_F.format(userkey=settings.USERKEY, appkey=settings.APPKEY)
        for id_ in ids:
            url = url_to_format.format(id=id_)
            try:
                Request.get_json(url, exit_=False, headers=auth.apisign(url, settings.SECRETKEY))
            except ValueError:
                logging.debug('Entry not deleted or not in favorites: ' + url)


class HtmlCommand(AbsCommand):
    name = 'html'

    def execute(self, arg, *args):
        arg = arg if arg is not True else None
        HtmlFile(tag=arg).create()
        sys.exit()


class SaveCommand(AbsCommand):
    name = 'save'

    def execute(self, *args):
        logging.info('...pobieranie plików z bazy danych')
        db_entries = DB.get_all_entries_with_comments()
        multi = Multi(5, save_wrapper, exts=settings.EXTS)
        with multi as mlt:
            for entry in db_entries:
                if entry.media_url:
                    mlt.put(entry.download_info())
                for comment in entry.comments:
                    if comment.media_url and not settings.SKIP_FILES == 'com':
                        mlt.put(comment.download_info())
        multi.join()
        sys.exit()


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

    def execute(self, arg, *args):
        settings.SKIP_FILES = arg


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
        ids = Decision(msg, {'0': sys.exit}, validator=ids_validator).run()
        settings.SOURCE = {'ids': ids}
        settings.STRATEGY = SourceStrategy


class UpdateCommand(AbsCommand):
    name = 'update'

    msg_err = 'Wystąpił problem z aktualizacją. Spróbuj ponownie lub pobierz samodzielnie.'

    def __init__(self):
        self.master_zip_url = settings.GITHUB_MASTER_ZIP_URL
        self.selenium_drivers_path = os.path.join(settings.BASE_DIR,
                                                  settings.SELENIUM_DRIVER_DIR_NAME)
        self.save_file = Save.save_single_file
        self.base_dir = settings.BASE_DIR
        _, self.file_name = os.path.split(self.master_zip_url)

    def execute(self, arg, *args):
        logging.warning('Wcześniej pobrane sterowniki przeglądarki zostaną usunięte.')
        if self.choose():
            self.save_and_unpack()
            self.delete_selenium_driver_files()
            logging.info('...aktualizacja przebiegła pomyślnie')
        sys.exit()

    def choose(self):
        msg = '{}\nChcesz pobrać powyższy plik i kontunuować aktualizację? ' \
              '(T/n): '.format(self.master_zip_url)
        dec = Decision(msg, {'T': True, 'n': sys.exit})
        return dec.run()

    def save_and_unpack(self):
        with tempfile.TemporaryDirectory() as tempdir:
            full_path = os.path.join(tempdir, self.file_name)
            if not self.save_file(self.master_zip_url, full_path):
                logging.critical(self.msg_err)
                raise SystemExit
            unpack_archive(full_path, tempdir, 'zip', self.msg_err)
            taktyk_path = os.path.join(tempdir, 'taktyk-master', 'taktyk')
            copy_tree(taktyk_path, self.base_dir)

    def delete_selenium_driver_files(self):
        if os.path.exists(self.selenium_drivers_path):
            shutil.rmtree(self.selenium_drivers_path)
