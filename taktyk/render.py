import logging
import os
import time

try:
    import jinja2
except ImportError:
    logging.debug('ImportError - jinja2 - ' + __file__)

from . import settings
from .db import DB


class HtmlFile:
    def __init__(self, tag=None):
        self.tag = tag
        self.user_files_path = settings.USER_FILES_PATH
        self.templates_path = settings.TEMPLATES_PATH
        self.template_name = settings.TEMPLATE_NAME
        self.file_name = None

    def create_file_name(self):
        self.file_name = 'taktyk-{}.html'.format(time.strftime('%Y.%m.%d_%H-%M-%S'))
        return self.file_name

    def get_full_path(self):
        return os.path.join(self.user_files_path, self.create_file_name())

    def render(self, tags, entries):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.templates_path))
        try:
            template = env.get_template(self.template_name)
        except jinja2.exceptions.TemplateNotFound:
            logging.critical('Nie odnaleziono pliku: %s', self.template_name)
            raise SystemExit
        else:
            rendered = template.render(tags=tags, entries=entries)
            rendered_bytes = rendered.encode('utf-8')
            return rendered_bytes

    def save(self, rendered_bytes):
        with open(self.get_full_path(), 'wb') as html_file:
            html_file.write(rendered_bytes)

    def create(self):
        logging.info('...tworzenie pliku html')
        with DB.Connect() as cursor:
            tags = DB.count_tags(cursor, self.tag)
            entries = DB.get_all_entries_with_comments(cursor, self.tag)
            rendered_bytes = self.render(tags, entries)
            self.save(rendered_bytes)
        logging.info('...utworzono plik html: %s', self.file_name)
