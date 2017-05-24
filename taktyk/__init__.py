__author__ = 'github.com/kosior'
__license__ = 'MIT'
__version__ = '0.2.0'

import logging

try:
    import readline  # user input history
except ImportError:
    pass

import signal
import sys
from . import settings
from .args import process_args
from .db import DB
from .render import HtmlFile
from .save import Multi, save_wrapper
from .utils import configure_logging, ex_hook


def pipeline(strategy, method):
    progress_info = '\rIlość wpisów: {}      Ilość komentarzy: {}'
    if settings.SKIP_FILES:
        proc_count = 0
    else:
        proc_count = 5

    with DB.Connect() as cursor, Multi(proc_count, save_wrapper) as mlt:
        settings.DB_IDS = DB.get_ids(cursor, 'entry')
        for raw_entry in strategy().execute():
            for entry in method().generate(raw_entry):
                DB.insert_one(cursor, entry)
                print(progress_info.format(settings.ENTRIES_ADDED, settings.COMMENTS_ADDED), end='')
                if entry.media_url and not settings.SKIP_FILES:
                    mlt.put(entry.download_info())

    if settings.ENTRIES_ADDED or settings.COMMENTS_ADDED:
        print()  # for better display
    else:
        logging.info('...nie dodano żadnych wpisów ani komentarzy')


def main():
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(''))  # handling KeyboardInterrupt
    sys.excepthook = ex_hook  # creating hook for uncaught exceptions
    configure_logging()
    process_args(settings.STATIC_ARGS)
    pipeline(settings.STRATEGY, settings.METHOD)
    HtmlFile().create()
