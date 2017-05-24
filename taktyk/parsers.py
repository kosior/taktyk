import logging

try:
    import bs4
except ImportError:
    logging.debug('ImportError - bs4 - ' + __file__)

from . import settings
from .entry import Entry


class JsonParser:
    def __init__(self, json_):
        assert isinstance(json_, dict)
        self.json_ = json_
        self.entry_url = settings.ENTRY_URL
        self.entry = Entry()
        self.entry.id_ = json_.get('id')
        self.entry.type_ = json_.get('type')

    def _parse_static(self, json_):
        self.entry.author = json_.get('author')
        self.entry.date = json_.get('date')
        self.entry.plus = str(json_.get('vote_count'))

        if self.entry.type_ == 'entry_comment':
            self.entry.entry_id = json_.get('entry_id')
            self.entry.url = '{}{}/#comment-{}'.format(self.entry_url, self.entry.entry_id,
                                                       self.entry.id_)
        else:
            self.entry.url = self.entry_url + str(self.entry.id_)

        if json_.get('embed'):
            self.entry.media_url = json_.get('embed', {}).get('url')

    def _parse_body_and_tags(self, json_):
        tags = []
        body_html = json_.get('body')
        body = bs4.BeautifulSoup('<html>{}</html>'.format(body_html), 'html.parser')
        hrefs = [a.get('href') for a in body.find_all('a')]

        for href in hrefs:
            if href.startswith('#'):
                body_html = body_html.replace(href, 'https://www.wykop.pl/tag/{}'.format(href[1:]))
                tags.append(href.strip('#'))
            elif href.startswith('@'):
                body_html = body_html.replace(href, 'https://www.wykop.pl/ludzie/{}'.format(href[1:]))

        self.entry.body_html = body_html
        self.entry.body = ''.join(body.find_all(text=True))
        if tags:
            self.entry.tags = ' '.join(tags)
        else:
            self.entry.tags = '#'

    def _parse_nsfw(self, json_, tags):
        self.entry.is_nsfw = False
        if json_.get('embed'):
            self.entry.is_nsfw = json_.get('embed', {}).get('plus18')
        if not self.entry.is_nsfw:
            if 'nsfw' in tags:
                self.entry.is_nsfw = True

    def parse(self):
        self._parse_static(self.json_)
        self._parse_body_and_tags(self.json_)
        self._parse_nsfw(self.json_, self.entry.tags)
        return self.entry


class SingleEntryHtmlParser:
    def __init__(self, id_, entry_tag):
        assert isinstance(entry_tag, bs4.element.Tag)
        self.main_entry_id = id_
        self.entry_tag = entry_tag
        self.entry_url = settings.ENTRY_URL
        self.entry = Entry(id_=self.get_id())

    def parse(self):
        try:
            self._set_type_and_url()
            self.entry.author = self.get_author()
            self.entry.date = self.get_date()
            self.set_body_and_body_html()
            self.entry.plus = self.get_plus()
            self.entry.media_url = self.get_media_url()
            self.entry.tags = self.get_tags()
            self.entry.is_nsfw = self.get_is_nsfw()
        except AttributeError:
            return None
        else:
            return self.entry

    def get_id(self):
        try:
            id_ = int(self.entry_tag.get('data-id'))
        except TypeError:
            return None
        else:
            return id_

    def get_author(self):
        return self.entry_tag.find(class_='showProfileSummary').get_text()

    def get_date(self):
        return self.entry_tag.find('time').get('title')

    def set_body_and_body_html(self):
        body = self.entry_tag.find(class_='text').find('p')
        for a in body.find_all('a', class_='showSpoiler'):  # deleting 'pokaż spoiler'
            a.decompose()
        body_html = str(body)
        body_html = body_html.replace('<p>', '')
        body_html = body_html.replace('</p>', '')
        body_html = body_html.replace('class="showTagSummary"', '')
        body_html = body_html.strip()
        body = body.get_text().strip()

        self.entry.body_html = body_html
        self.entry.body = body

    def get_plus(self):
        return self.entry_tag.find(class_='vC').get('data-vc')

    def get_media_url(self):
        media_url = self.entry_tag.find(class_='media-content')
        if media_url:
            return media_url.find('a').get('href')
        return ''

    def get_tags(self):
        tags = self.entry_tag.find(class_='text').find_all(class_='showTagSummary')
        tags = [tag.get_text() for tag in tags]
        if tags:
            return ' '.join(tags)
        return '#'

    def get_is_nsfw(self):
        if self.entry_tag.find(class_='plus18item'):
            return True
        if 'nsfw' in self.entry.tags:
            return True
        return False

    def _set_type_and_url(self):
        if self.entry.id_ == int(self.main_entry_id):
            self.entry.type_ = 'entry'
            self.entry.url = self.entry_url + str(self.entry.id_)
        else:
            self.entry.type_ = 'entry_comment'
            self.entry.entry_id = self.main_entry_id
            self.entry.url = '{}{}/#comment-{}'.format(self.entry_url, self.entry.entry_id,
                                                       self.entry.id_)


class HtmlParser:
    def __init__(self, id_, html, helper=None):
        self.id_ = id_
        self.html = html
        self.soup_list = self.get_entries_soup_list()
        self.EntryParserHelper = helper or SingleEntryHtmlParser

    def get_entries_soup_list(self):
        soup = bs4.BeautifulSoup(self.html, 'html.parser')
        soup = soup.find(class_='entry')
        if soup:
            soup = soup.find_all(class_='lcontrast')  # list of entry and comments
            return soup if soup else None

    def get_main_entry(self):
        if self.soup_list:
            self.EntryParserHelper(self.id_, self.soup_list[0]).parse()
            parser = self.EntryParserHelper(self.id_, self.soup_list[0])
            if parser.entry.id_:
                return parser.parse()
            return None

    def get_comments_generator(self, start_index):
        if self.soup_list:
            for comment_soup in self.soup_list[start_index:]:
                parser = self.EntryParserHelper(self.id_, comment_soup)
                if parser.entry.id_:
                    yield parser.parse()
                else:
                    raise StopIteration('Problem with comment parsing.')

    @staticmethod
    def find_ids_in_html(page):
        ids = []
        page_soup = bs4.BeautifulSoup(page, 'html.parser')
        entries = page_soup.find_all(class_='entry iC ')

        for entry in entries:
            ids.append(entry.find('div').get('data-id'))
        return ids
