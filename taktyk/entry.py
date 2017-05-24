import os
from inspect import signature

from . import db
from . import settings


class Entry:
    def __init__(self, id_=None, author=None, date=None, body=None, body_html=None, url=None,
                 plus=None, media_url=None, tags=None, is_nsfw=None, entry_id=None, type_=None):
        self.id_ = id_
        self.author = author
        self.date = date
        self.body = body
        self.body_html = body_html
        self.url = url
        self.plus = plus
        self.media_url = media_url
        self.tags = tags
        self.is_nsfw = is_nsfw
        self.entry_id = entry_id  # only for comment
        self.type_ = type_

    def __iter__(self):
        return self.attrs_gen()

    def attrs_gen(self):
        attrs = list(signature(self.__init__).parameters.keys())  # attributes from __init__()
        return (getattr(self, attr) for attr in attrs[:11])

    def __str__(self):
        if self.entry_id:
            return '{}_{}'.format(self.entry_id, self.id_)
        return str(self.id_)

    def download_info(self):
        return {
            'id_': self.__str__(),
            'media_url': self.media_url,
            'is_nsfw': self.is_nsfw,
            'local_file_path': self.local_file_path,
        }

    @property
    def comments_count(self):
        if not self.entry_id:  # if entry_id is not none it's a comment
            return db.DB.count_comments(self.id_)

    @property
    def media_ext(self):
        if self.media_url:
            _, ext = os.path.splitext(self.media_url)
            if len(ext) > 4 and '?' in ext:  # fix for urls with '?'
                ext = ext.split('?')[0]
            elif not ext and 'gfycat.com' in self.media_url:
                ext = '.webm'
            return ext
        else:
            return None

    @property
    def local_file_path(self):
        path = settings.FILES_DIR_NAME
        ext = self.media_ext

        if self.media_url and ext:
            if self.is_nsfw:
                path = os.path.join(path, settings.NSFW_DIR_NAME)
            if self.entry_id:  # it's a comment
                return os.path.join(path, settings.COMMENTS_DIR_NAME,
                                    '{}_{}{}'.format(self.entry_id, self.id_, ext))
            return os.path.join(path, '{}{}'.format(self.id_, ext))
        return ''
