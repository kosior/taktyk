from . import settings
from .auth import apisign
from .request import Request


class ApiContent:
    def __init__(self, appkey=None, userkey=None, secret=None):
        self.appkey = appkey or settings.APPKEY
        self.userkey = userkey or settings.USERKEY
        self.secret = secret or settings.SECRETKEY
        self.page_num = 1
        self.fav_url = settings.API_FAVORITES_URL_F.format(userkey=self.userkey, appkey=self.appkey)
        self.entry_url = settings.API_ENTRY_URL_F.format(appkey=self.appkey)

    def gen_entries(self):
        while True:
            url = self.fav_url + str(self.page_num)
            self.page_num += 1
            try:
                entries_json = Request.get_json(url, exit_=False, headers=apisign(url, self.secret))
            except ValueError:
                break
            else:
                if not entries_json:
                    break
                yield entries_json

    def gen_entries_by_ids(self, ids):
        for id_ in ids:
            yield self.get_one_entry(id_)

    def get_one_entry(self, id_):
        url = self.entry_url.format(index=id_)
        try:
            entry_json = Request.get_json(url, exit_=False, headers=apisign(url, self.secret))
        except ValueError:
            return []
        else:
            return entry_json


class HtmlContent:
    def __init__(self):
        self.entry_url = settings.ENTRY_URL

    def gen_html_entries_by_ids(self, ids):
        for id_ in ids:
            raw_entry = self.get_entry(id_)
            if raw_entry:
                yield id_, raw_entry

    def get_entry(self, id_):
        entry_url = self.entry_url + id_
        response = Request.get(entry_url, exit_=False)
        try:
            return response.text
        except AttributeError:
            return []
