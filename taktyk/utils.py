import configparser
import logging
import os
import shutil
import traceback

from . import settings


class CustomFormatter(logging.Formatter):
    FORMATS = {logging.DEBUG: 'DEBUG: %(module)s: %(lineno)d: %(message)s',
               logging.INFO: '%(message)s',
               logging.WARNING: 'UWAGA! %(message)s',
               # logging.ERROR: 'ERROR: %(message)s',
               # logging.CRITICAL: 'CRITICAL: %(message)s'
               }

    def __init__(self):
        super().__init__(fmt="%(levelname)s: %(message)s", datefmt=None, style='%')

    def format(self, record):
        fmt = self._style._fmt
        self._style._fmt = self.FORMATS.get(record.levelno, fmt)
        result = logging.Formatter.format(self, record)
        self._style._fmt = fmt
        return result


def configure_logging():
    log_file_path = os.path.join(settings.BASE_DIR, 'taktyk.log')

    def get_save_mode(path):
        if os.path.isfile(path) and os.path.getsize(path) > 1048576:
            return 'w'
        return 'a'

    logger = logging.getLogger()
    logger.handlers = []
    logger.setLevel(logging.DEBUG)

    custom_fmt = CustomFormatter()
    formatter = logging.Formatter('%(levelname)s: %(module)s: %(lineno)d: %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(custom_fmt)

    fh = logging.FileHandler(log_file_path, mode=get_save_mode(log_file_path))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    requests_logger = logging.getLogger('requests')
    requests_logger.propagate = False

    logging.debug('\n-------------------------------NEW EXECUTION-------------------------------\n')


def ex_hook(ex_cls, ex, tb):
    logging.debug(' '.join(traceback.format_tb(tb)))
    logging.debug('%s %s', ex_cls, ex)
    logging.critical('Nieznany błąd: %s: %s', ex_cls.__name__, ex)


class Decision:
    """
    Class for custom prompts
        options - dictionary options {'Y': {func: *args}, 'n': exit}
            if input == 'Y' --> execute func with args - func(*args)
            if input == 'n' --> exit()

        validator (optional) - pass function to validate input and if validation passes,
                               input will be returned
                               (to get any input set 'validator=lambda x: x' in __init__)
    """
    def __init__(self, msg, options=None, validator=None):
        self.msg = msg
        self._options = options
        self.validator = validator

    @property
    def options(self):
        return {k.lower(): v for k, v in self._options.items()} if self._options else {}

    @options.setter
    def options(self, value):
        self._options = value

    @staticmethod
    def _run_func(func):
        if isinstance(func, dict):
            for k, v in func.items():
                return k(*v)
        elif func:
            return func()
        return True

    def run(self):
        while True:
            answer = input(self.msg)
            answer_low = answer.lower()
            if answer_low in self.options.keys():
                if callable(self.options[answer_low]) or isinstance(self.options[answer_low], dict):
                    return self._run_func(self.options[answer_low])
                return self.options[answer_low]
            elif self.validator:
                try:
                    result = self.validator(answer)
                except ValueError as err:
                    logging.error(err.__str__())
                else:
                    return result
            else:
                msg = 'Zły wybór! Wybierz jeszcze raz.'
                logging.error(msg)


def unpack_archive(file, extract_dir, format_, msg):
    try:
        shutil.unpack_archive(file, extract_dir=extract_dir, format=format_)
    except (ValueError, OSError) as err:
        logging.debug(traceback.format_exc())
        logging.critical(err)
        logging.critical(msg)
        raise SystemExit


class ConfigFile:
    template = [
        ['DANE LOGOWANIA', [
            ['username', ''],
            ['password', '']
        ]],
        ['WykopAPI', [
            ['appkey', ''],
            ['secretkey', ''],
            ['accountkey', ''],
            ['# opcjonalnie:'],
            ['userkey', '']
        ]],
        ['ARGUMENTY', [
            ['# przykład: static_args = -s chrome --skip -n'],
            ['static_args', '']
        ]],
        ['POBIERANE ROZSZERZENIA', [
            ['exts', '.gif .jpg .jpeg .png .webm']
        ]]
    ]

    def __init__(self):
        self.file_path = os.path.join(settings.BASE_DIR, settings.CONFIG_FILE)
        self.config = configparser.ConfigParser(allow_no_value=True)

    def prepare(self):
        for section, options_and_values in self.template:
            self.config.add_section(section)
            for opt_val in options_and_values:
                self.config.set(section, *opt_val)

    def create_configfile(self):
        with open(self.file_path, 'w') as configfile:
            self.config.write(configfile)

    def read_and_apply_config(self):
        self.config.read(self.file_path)
        for section in self.config.sections():
            for option in self.config[section]:
                value = self.config.get(section, option)
                if value:
                    if option in ('static_args', 'exts'):
                        value = value.split(' ')
                    setattr(settings, option.upper(), value)

    def set_up(self):
        if os.path.isfile(self.file_path):
            self.read_and_apply_config()
        else:
            self.prepare()
            self.create_configfile()
