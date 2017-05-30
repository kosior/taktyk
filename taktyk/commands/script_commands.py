import importlib
import logging
import os
import sys

try:
    import pip
except ImportError:
    logging.debug('ImportError - pip - ' + __file__)

from .abs_base import AbsCommand
from .. import __version__, settings
from ..auth import is_key_valid
from ..db import database_list, DB
from ..entrygenerators import APIMethod, ScrapeMethod
from ..request import Request
from ..strategies import APIStrategy, SessionStrategy
from ..utils import Decision


class ConfigureCommand(AbsCommand):
    name = 'Configure'

    def execute(self, *args):
        self.set_strategy_and_method()

    @staticmethod
    def set_strategy_and_method():
        if is_key_valid(settings.APPKEY):
            settings.STRATEGY = APIStrategy
            settings.METHOD = APIMethod
        else:
            logging.warning('Wystąpił problem z Wykop API. Program przełączy się na tryb scrapowania.')
            logging.warning('Problem mógł być spowodowany wprowadzeniem zmian w pliku config.ini.')
            settings.SCRAPE = True
            settings.STRATEGY = SessionStrategy
            settings.METHOD = ScrapeMethod


class ModulesHandler(AbsCommand):
    name = 'ModulesHandler'

    def __init__(self, to_import=None):
        self.to_import = to_import or settings.MODULES
        self.unimported = []

    def execute(self, *args):
        logging.info('...sprawdzanie modułów')
        self.import_all()
        if self.unimported:
            self.process_unimported()

    def import_all(self, reload=False):
        import_flags = []
        for import_name, install_name, version in self.to_import:
            import_flags.append(self.try_import(import_name, install_name, version=version,
                                                reload=reload))
        return import_flags

    def try_import(self, import_name, install_name=None, version=None, add=True, reload=False):
        try:
            imported = importlib.import_module(import_name)
            if reload:
                imported = importlib.reload(imported)
        except ImportError:
            if add:
                self.unimported.append([import_name, install_name, version])
            return False
        else:
            if version and imported.__version__ != version:
                self.unimported.append([import_name, install_name, version])
                return False
            return True

    def process_unimported(self):
        msg = 'Brak modułu pip!\nNie można zainstalować:\n%s'
        msg_dec = 'Wymagane moduły:\n{}\nChcesz zainstalować (T/n)? '
        self.to_import = list(self.unimported)
        modules_text = '\n'.join([' {} - {}'.format(ins, ver) for _, ins, ver in self.unimported])
        if self.try_import('pip', add=False):
            msg_dec = msg_dec.format(modules_text)
            decision = Decision(msg_dec, {'T': {self.install_unimported: (self.unimported,)},
                                          'n': exit})
            decision.run()
            if all(self.import_all(reload=True)):
                logging.info('...ponowne uruchamianie')
                os.execv(sys.executable, ['python'] + sys.argv)
            else:
                logging.critical('Nie udało się zainstalować modułów.')
                raise SystemExit
        else:
            logging.critical(msg, modules_text)
            raise SystemExit

    @staticmethod
    def install_unimported(unimported):
        for _, install_name, version in unimported:
            if version:
                module = '{}=={}'.format(install_name, version)
            else:
                module = install_name
            pip.main(['install', module])


class CreateFolders(AbsCommand):
    name = 'CreateFolders'

    def execute(self, *args):
        for dirs in settings.dirs_to_create():
            path = os.path.join(settings.USER_FILES_PATH, *dirs)
            os.makedirs(path, exist_ok=True)


class CheckForUpdate(AbsCommand):
    name = 'CheckForUpdate'

    def __init__(self):
        self.local_version = __version__
        self.latest_release_url = settings.GITHUB_LATEST_RELEASE_URL

    def execute(self, *args):
        logging.info('...sprawdzanie aktualizacji')
        if self.is_new_version():
            self.notify()
        else:
            logging.info('...brak aktualizacji')

    def get_github_version(self):
        response = Request.get(self.latest_release_url,
                               msg='Wystąpił problem ze sprawdzaniem aktualizacji')
        try:
            return response.url.rsplit('/', 1)[-1]
        except AttributeError:
            return ''

    def is_new_version(self):
        return self.get_github_version() > self.local_version

    @staticmethod
    def notify():
        print('\n-------  Aktualizacja jest dostępna  -------\n'
              '--  Aby zaktualizować użyj parametru: -u  --\n')


class DBHandler(AbsCommand):
    name = 'DBHandler'

    def __init__(self):
        self.db_list = database_list(os.path.join(settings.USER_FILES_PATH, settings.DB_DIR_NAME))
        self.db_len = len(self.db_list)

    @staticmethod
    def set_db_name(db_name):
        settings.DB_NAME = db_name

    def choose(self):
        options = {'0': exit, 'n': DB.ask_and_create()}
        msg = '\n Wybierz bazę danych i naciśnij ENTER\n\n'
        for num, db_name in enumerate(self.db_list):
            options[str(num + 1)] = {self.set_db_name: (db_name,)}
            msg += ('   {} : {}\n'.format(num + 1, db_name))
        msg += '   n - utwórz nową bazę danych\n   0 - Wyjście.\n\n Wybór: '

        dec = Decision(msg, options)
        dec.run()

    def execute(self, *args):
        if self.db_len == 0:
            DB.create()
        elif self.db_len == 1:
            self.set_db_name(self.db_list[0])
        else:
            self.choose()
