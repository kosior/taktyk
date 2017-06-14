import logging
import multiprocessing
import os

from . import settings
from .request import Request


class Save:
    unsaved_file = 'niezapisane.txt'
    gfycat = 'gfycat.com/'
    msg = 'Plik niezapisany: '

    def __init__(self, id_, media_url, is_nsfw, local_file_path, exts, cwd=None):
        self.id_ = id_
        self.media_url = media_url
        self.is_nsfw = is_nsfw
        self.dir_path, self.file_name = os.path.split(local_file_path)
        self.exts = exts
        self.cwd = cwd or settings.USER_FILES_PATH
        self.gfycat_api = settings.GFYCAT_API
        self._ext = self.get_ext()
        self.url = self.get_file_url()
        self.nsfw_consistent = not(settings.NSFW_FILTER and self.is_nsfw)

    def get_path(self):
        full_path = os.path.join(self.cwd, self.dir_path)
        if os.path.exists(full_path):
            return os.path.join(full_path, self.file_name)
        return None

    def get_ext(self):
        _, ext = os.path.splitext(self.file_name)
        if ext in self.exts:
            return ext
        return None

    def get_gfycat_url(self):
        name = self.media_url.split(self.gfycat)[-1]
        try:
            json_ = Request.get_json(self.gfycat_api+name)
        except ValueError:
            self.save_to_text_file()
            return None
        else:
            return json_.get('gfyItem', {}).get('webmUrl')

    def get_file_url(self):
        if not self._ext:
            self.save_to_text_file()
            return None
        if self._ext == '.webm' and 'gfycat.com' in self.media_url:
            return self.get_gfycat_url()
        return self.media_url

    def save_to_text_file(self):
        full_path = os.path.join(self.cwd, self.unsaved_file)
        with open(full_path, 'a+') as file:
            file.write('{},{},{}\n'.format(self.id_, self.is_nsfw, self.media_url))

    def save(self):
        if self.url and self.nsfw_consistent:
            msg = self.msg + self.url
            full_path = self.get_path()
            if full_path:
                if os.path.exists(full_path):
                    logging.debug('File already exist')
                    return True
                return self.save_single_file(self.url, full_path, msg)
            else:
                logging.debug('Path not found: %s', self.file_name)
                return False

    @staticmethod
    def save_single_file(url, full_path, msg=''):
        response = Request.get(url, exit_=False, msg=msg, stream=True)
        try:
            response_gen = response.iter_content(1024)
        except AttributeError:
            return False

        with open(full_path, 'wb') as file:
            for chunk in response_gen:
                if chunk:
                    file.write(chunk)
            return True

    @staticmethod
    def save_text_file(url, full_path, msg=''):
        msg = msg + url
        response = Request.get(url, exit_=False, msg=msg)

        try:
            content = response.content
        except AttributeError:
            return False

        with open(full_path, 'wt') as file:
            file.write(content)
            return True


def save_wrapper(download_info_dict, kwargs):
    return Save(**download_info_dict, **kwargs).save()


class Multi:
    def __init__(self, count, func, end_clause='end', **func_kwargs):
        self.count = count
        self.func = func
        self.queue = multiprocessing.Queue()
        self.end_clause = end_clause
        self.func_kwargs = func_kwargs

    def __enter__(self):
        for _ in range(self.count):
            p = multiprocessing.Process(target=self._target,
                                        args=(self.queue, self.func, self.end_clause, self.func_kwargs))
            p.start()
        return self

    def __exit__(self, tp, v, tb):
        for _ in range(self.count):
            self.queue.put(self.end_clause)

    @staticmethod
    def _target(queue, func, end_clause, func_kwargs):
        while True:
            args = queue.get()
            if args == end_clause:
                break
            func(args, func_kwargs)

    def put(self, value):
        self.queue.put(value)
