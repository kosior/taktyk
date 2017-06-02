from concurrent import futures

from . import settings
from .auth import apisign
from .request import Request


def gen_entries_by_ids_with_futures(func, *args, ids=(), max_workers=0):
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures_lst = [executor.submit(func, *args, id_) for id_ in ids]
        for future in futures.as_completed(futures_lst):
            raw_entry = future.result()
            if raw_entry:
                yield raw_entry


class ApiContent:
    def __init__(self, appkey=None, userkey=None, secret=None):
        self.appkey = appkey or settings.APPKEY
        self.userkey = userkey or settings.USERKEY
        self.secret = secret or settings.SECRETKEY
        self.page_num = 0
        self.fav_url = settings.API_FAVORITES_URL_F.format(userkey=self.userkey, appkey=self.appkey)
        self.entry_url = settings.API_ENTRY_URL_F.format(appkey=self.appkey)

    def get_json(self, url_to_prepare, id_=None):
        if url_to_prepare == self.fav_url:
            url = url_to_prepare + str(self.page_num)
        elif url_to_prepare == self.entry_url and id_:
            url = url_to_prepare.format(index=id_)
        else:
            raise ValueError('Wrong url_to_prepare or id_ not set.')

        try:
            json_ = Request.get_json(url, exit_=False, headers=apisign(url, self.secret))
        except ValueError:
            return []
        else:
            return json_

    def submit_to_executor(self, executor):
        if self.page_num is not None:
            self.page_num += 1
            return executor.submit(self.get_json, self.fav_url)
        return False

    def gen_entries(self):
        with futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures_lst = [self.submit_to_executor(executor)]
            while futures_lst:
                future = self.submit_to_executor(executor)
                if future:
                    futures_lst.append(future)
                entry_json = futures_lst.pop(0).result()
                if entry_json:
                    yield entry_json
                else:
                    self.page_num = None

    def gen_entries_by_ids(self, ids):
        entry_json_gen = gen_entries_by_ids_with_futures(self.get_json, self.entry_url, ids=ids,
                                                         max_workers=5)
        for entry_json in entry_json_gen:
            yield entry_json


class HtmlContent:
    def __init__(self):
        self.entry_url = settings.ENTRY_URL_SCRAPE

    def get_entry(self, id_):
        entry_url = self.entry_url + id_
        response = Request.get(entry_url, exit_=False)
        try:
            return id_, response.text
        except AttributeError:
            return []

    def gen_html_entries_by_ids(self, ids):
        raw_entry_gen = gen_entries_by_ids_with_futures(self.get_entry, ids=ids, max_workers=5)
        for raw_entry in raw_entry_gen:
            yield raw_entry
