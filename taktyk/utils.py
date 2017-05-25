import logging
import os
import shutil
import traceback

from .settings import BASE_DIR


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
    log_file_path = os.path.join(BASE_DIR, 'taktyk.log')

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
            answer = input(self.msg).lower()
            if answer in self.options.keys():
                if callable(self.options[answer]) or isinstance(self.options[answer], dict):
                    return self._run_func(self.options[answer])
                return self.options[answer]
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
