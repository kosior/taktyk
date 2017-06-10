import logging
import os
import platform
import stat
import sys
import tempfile
import traceback

from . import settings
from .request import Request
from .save import Save
from .utils import Decision, unpack_archive


class SeleniumDriver:
    msg = '''Wystąpił problem ze sterownikiem przeglądarki
        Zaktualizuj przeglądarkę.
        Pobierz najnowszy sterownik ręcznie i rozpakuj do folderu seleniumdrivers:
             firefox: https://github.com/mozilla/geckodriver/releases
             chrome: https://sites.google.com/a/chromium.org/chromedriver/downloads'''

    def __init__(self, browser, file_name, sfx, driver_url=None, folder_path=None,
                 save_file_func=None):
        self.browser = browser
        self.file_name = file_name
        self.sfx = sfx
        self.driver_url = driver_url or settings.SELENIUM_DRIVER_URLS.get(browser)
        self.folder_path = folder_path or os.path.join(settings.BASE_DIR,
                                                       settings.SELENIUM_DRIVER_DIR_NAME)
        self.download_url = None
        self.save_file_func = save_file_func or Save.save_single_file

    def get_download_url(self):
        raise NotImplementedError

    def set_driver_path(self):
        path = os.path.join(self.folder_path, self.file_name)
        if os.path.isfile(path):
            settings.SELENIUM_DRIVER_PATH = path
            return True
        elif os.path.isfile(path[:-4]):
            settings.SELENIUM_DRIVER_PATH = path[:-4]
            return True
        return False

    def get_suffix(self):
        system = platform.system()
        arch = platform.architecture()[0].replace('bit', '')
        return self.sfx.get(system).format(arch)

    @staticmethod
    def get_format(url):
        if url.endswith('tar.gz'):
            return 'gztar'
        elif url.endswith('.zip'):
            return 'zip'
        return None

    @staticmethod
    def make_executable(driver_path):
        st = os.stat(driver_path)
        os.chmod(driver_path, st.st_mode | stat.S_IEXEC)

    def download_and_unpack(self):
        fmt = self.get_format(self.download_url)
        with tempfile.TemporaryDirectory() as tempdir:
            file_name = self.download_url.rsplit('/', 1)[-1]
            full_path = os.path.join(tempdir, file_name)
            logging.info('...pobieranie sterownika')
            if not self.save_file_func(self.download_url, full_path):
                logging.CRITICAL(self.msg)
                raise SystemExit
            logging.info('...rozpakowywanie archiwum')
            unpack_archive(full_path, self.folder_path, fmt, self.msg)

    def choose(self):
        msg = '{}\nChcesz pobrać powyższy plik? (T/n): '.format(self.download_url)
        dec = Decision(msg, options={'T': True, 'n': sys.exit})
        return dec.run()

    def get_driver(self):
        self.download_url = self.get_download_url()
        if self.choose():
            self.download_and_unpack()
            self.set_driver_path()
            self.make_executable(settings.SELENIUM_DRIVER_PATH)

    def prepare(self):
        if not self.set_driver_path():
            if not os.path.exists(self.folder_path):
                os.makedirs(self.folder_path, exist_ok=True)
            self.get_driver()


class ChromeDriver(SeleniumDriver):
    name = 'chrome'
    driver_file_name = 'chromedriver.exe'
    sfx = {
        'Linux': 'linux{}.zip',
        'Windows': 'win32.zip',
        'Darwin': 'mac64.zip',
    }

    def __init__(self):
        super().__init__(browser=self.name, file_name=self.driver_file_name, sfx=self.sfx)

    def get_download_url(self):
        suffix = self.get_suffix()
        response = Request.get(self.driver_url + '/LATEST_RELEASE', exit_=True, msg=self.msg)
        try:
            ver = response.text.strip()
        except AttributeError as err:
            logging.debug(traceback.format_exc())
            logging.critical(err)
            print(self.msg)
            raise SystemExit
        else:
            return '{url}/{ver}/chromedriver_{suffix}'.format(url=self.driver_url, ver=ver,
                                                              suffix=suffix)


class FirefoxDriver(SeleniumDriver):
    name = 'firefox'
    driver_file_name = 'geckodriver.exe'
    sfx = {
        'Linux': 'linux{}.tar.gz',
        'Windows': 'win{}.zip',
        'Darwin': 'macos.tar.gz'
    }

    def __init__(self):
        super().__init__(browser=self.name, file_name=self.driver_file_name, sfx=self.sfx)

    def get_download_url(self):
        suffix = self.get_suffix()
        response = Request.get(self.driver_url + '/latest', exit_=True, msg=self.msg)
        try:
            ver = response.url.split('/')[-1]
        except AttributeError as err:
            logging.debug(traceback.format_exc())
            logging.critical(err)
            print(self.msg)
            raise SystemExit
        else:
            return '{url}/download/{ver}/geckodriver-{ver}-{suffix}'.format(url=self.driver_url,
                                                                            ver=ver, suffix=suffix)


class DriverManager:
    msg = SeleniumDriver.msg

    def __init__(self, browser):
        self.browser = browser

    def run(self):
        for subclass in SeleniumDriver.__subclasses__():
            if subclass.name == self.browser:
                subclass().prepare()
                break
