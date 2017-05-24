import abc
import logging
import os
import re

try:
    import selenium
    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException, NoSuchElementException
except ImportError:
    logging.debug('ImportError - selenium - ' + __file__)

from . import settings
from .auth import set_userkey, log_in_for_session
from .contentdelivery import ApiContent, HtmlContent
from .parsers import HtmlParser
from .seleniumdriver import DriverManager


class Strategy(metaclass=abc.ABCMeta):
    def execute(self):
        pass

    @staticmethod
    def get_content_by_ids(ids):
        if settings.SCRAPE:
            return HtmlContent().gen_html_entries_by_ids(ids)
        return ApiContent().gen_entries_by_ids(ids)


class APIStrategy(Strategy):
    def execute(self):
        logging.info('...uruchamianie APIStrategy')
        logging.info('...rozpoczęcie uwierzytelniania')
        set_userkey()
        logging.info('...pobieranie numerów id i generowanie wpisów')
        return ApiContent(userkey=settings.USERKEY).gen_entries()


class SourceStrategy(Strategy):
    def execute(self):
        logging.info('...uruchamianie SourceStrategy')
        logging.info('...pobieranie numerów id')
        opt = {'file': self.get_ids_from_file, 'dir': self.get_ids_from_dir, 'ids': lambda x: x}
        for key, value in settings.SOURCE.items():
            get_ids_func = opt[key]
            ids = get_ids_func(value)
            if not ids:
                logging.error('Nie znaleziono numerów id.')
                raise SystemExit
            logging.info('...ilość znalezionych numerów id: %s', len(ids))
            logging.info('...generowanie wpisów')
            return self.get_content_by_ids(ids)

    @staticmethod
    def get_ids_from_file(path):
        entry_id_regex = re.compile(r'wpis/(\d+)/|(?:\s{1}|^|,)(\d+)(?:(?=\s{1}|$|,))')
        try:
            with open(path, 'rt') as file:
                ids_lst = entry_id_regex.findall(file.read())
            return [id_ for id_tuple in ids_lst for id_ in id_tuple if id_]
        except (OSError, ValueError):
            return []

    @classmethod
    def get_ids_from_dir(cls, path):
        ids = []
        files = [os.path.join(path, file) for file in os.listdir(path)]

        for file in files:
            if file.endswith('html') or file.endswith('htm'):
                with open(file, 'rb') as page:
                    ids.extend(HtmlParser.find_ids_in_html(page))
            else:
                ids.extend(cls.get_ids_from_file(file))
        return ids


class SeleniumStrategy(Strategy):
    def __init__(self):
        self.cls_options = {'firefox': selenium.webdriver.Firefox,
                            'chrome': selenium.webdriver.Chrome}
        DriverManager(settings.BROWSER).run()
        self.webdriver_cls = self.cls_options[settings.BROWSER]
        self.driver = None

    def open_browser(self):
        try:
            self.driver = self.webdriver_cls(executable_path=settings.SELENIUM_DRIVER_PATH)
        except (FileNotFoundError, WebDriverException) as err:
            print(DriverManager.msg)
            logging.debug(err)
            raise SystemExit

    def execute(self):
        logging.info('...uruchamianie SeleniumStrategy')
        logging.info('...uruchamianie przeglądarki - %s', settings.BROWSER)
        self.open_browser()
        try:
            self.driver.get(settings.LOGIN_URL)
            self.log_in()
            logging.info('...pobieranie numerów id')
            ids = self.get_ids()
            self.driver.quit()
            logging.info('...generowanie wpisów')
            return self.get_content_by_ids(ids)
        except WebDriverException:
            logging.warning('Logowanie nie powiodło się.')
            try:
                self.driver.quit()
            except WebDriverException:
                pass
            raise SystemExit

    def log_in(self):
        wait = webdriver.support.ui.WebDriverWait(self.driver, 60)
        wait.until(lambda d: self.driver.find_element_by_class_name('logged-user'))

    def get_login(self):
        try:
            login = self.driver.find_element_by_class_name('avatar')
            return login.get_attribute('alt')
        except (NoSuchElementException, AttributeError) as err:
            logging.critical('Nie odnaleziono loginu.')
            logging.debug(err)
            raise SystemExit

    def get_ids(self):
        ids = []
        page_num = 1

        url = settings.FAVORITES_URL_F.format(username=self.get_login())

        while True:
            full_url = url + str(page_num)
            self.driver.get(full_url)
            page = self.driver.page_source

            new_ids = HtmlParser.find_ids_in_html(page)

            if new_ids:
                ids.extend(new_ids)
                page_num += 1
            else:
                break
        return ids


class SessionStrategy(Strategy):
    def execute(self):
        logging.info('...uruchamianie SessionStrategy')
        logging.info('...rozpoczęcie logowania')
        session = log_in_for_session()
        logging.info('...pobieranie numerów id')
        ids = self.process_session(session)
        logging.info('...generowanie wpisów')
        return self.get_content_by_ids(ids)

    @staticmethod
    def process_session(session):
        ids = []
        page_num = 1
        url = settings.FAVORITES_URL_F.format(username=settings.USERNAME)

        while True:
            full_url = url + str(page_num)
            page = session.get(full_url, headers=dict(referer=full_url))

            new_ids = HtmlParser.find_ids_in_html(page.text)

            if new_ids:
                ids.extend(new_ids)
                page_num += 1
            else:
                break
        return ids
