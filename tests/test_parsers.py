import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.parsers import JsonParser, HtmlParser


class JsonParserInitTest(unittest.TestCase):
    def test_init_assert_json(self):
        with self.assertRaises(AssertionError):
            JsonParser([])

    def test_init_id_and_type_in_json(self):
        json_ = {'id': 123, 'type': 'entry'}
        js = JsonParser(json_)
        self.assertEqual(123, js.entry.id_)
        self.assertEqual('entry', js.entry.type_)

    def test_init_id_and_type_not_in_json(self):
        json_ = {}
        js = JsonParser(json_)
        self.assertIsNone(js.entry.id_)
        self.assertIsNone(js.entry.type_)


class JsonParserParseStaticTest(unittest.TestCase):
    def test_if_author_date_plus_parsed(self):
        json_ = {'author': 'test_a', 'date': 'test_date', 'vote_count': 12}
        js = JsonParser(json_)
        js._parse_static()
        self.assertEqual('test_a', js.entry.author)
        self.assertEqual('test_date', js.entry.date)
        self.assertEqual('12', js.entry.plus)

    def test_when_type_is_entry_comment(self):
        json_ = {'type': 'entry_comment', 'entry_id': 55}
        js = JsonParser(json_)
        js._parse_static()
        self.assertEqual('entry_comment', js.entry.type_)
        self.assertEqual(55, js.entry.entry_id)
        self.assertTrue('#comment-{}'.format(js.entry.id_) in js.entry.url)

    def test_when_type_is_entry(self):
        json_ = {'type': 'entry', 'id': 1}
        js = JsonParser(json_)
        js._parse_static()
        self.assertEqual('entry', js.entry.type_)
        self.assertEqual(1, js.entry.id_)
        self.assertTrue('1' in js.entry.url)
        self.assertIsNone(js.entry.entry_id)

    def test_when_embed_present(self):
        json_ = {'embed': {'url': 'someurl'}}
        js = JsonParser(json_)
        js._parse_static()
        self.assertEqual('someurl', js.entry.media_url)


class JsonParserParseBodyAndTagsTest(unittest.TestCase):
    body = '<div>#<a href="#programowanie">programowanie</a> test text ' \
           '@<a href="@test_user">test_user</a> #<a href="#python">python</a></div>'

    def test_if_tags_parsed_correctly(self):
        json_ = {'body': self.body}
        js = JsonParser(json_)
        js._parse_body_and_tags()
        self.assertEqual(' programowanie python ', js.entry.tags)

    def test_if_no_tags_in_body(self):
        json_ = {'body': ''}
        js = JsonParser(json_)
        js._parse_body_and_tags()
        self.assertEqual(' # ', js.entry.tags)

    def test_href_replacements(self):
        json_ = {'body': self.body}
        js = JsonParser(json_)
        js._parse_body_and_tags()
        self.assertTrue('https://www.wykop.pl/tag/python' in js.entry.body_html)
        self.assertTrue('https://www.wykop.pl/ludzie/test_user' in js.entry.body_html)

    def test_if_body_parsed_correctly(self):
        json_ = {'body': self.body}
        js = JsonParser(json_)
        js._parse_body_and_tags()
        self.assertEqual('#programowanie test text @test_user #python', js.entry.body)


class JsonParserParseNsfwTest(unittest.TestCase):
    def test_when_embed(self):
        json_ = {'embed': {'plus18': True}}
        js = JsonParser(json_)
        js.entry.tags = ''
        js._parse_nsfw()
        self.assertTrue(js.entry.is_nsfw)

    def test_when_no_embed_no_tags(self):
        json_ = {}
        js = JsonParser(json_)
        js.entry.tags = ''
        js._parse_nsfw()
        self.assertFalse(js.entry.is_nsfw)

    def test_when_tags_with_nsfw_and_no_embed(self):
        json_ = {}
        js = JsonParser(json_)
        js.entry.tags = ' nsfw '
        js._parse_nsfw()
        self.assertTrue(js.entry.is_nsfw)

    def test_when_tags_without_nsfw_and_no_embed(self):
        json_ = {}
        js = JsonParser(json_)
        js.entry.tags = ' programowanie '
        js._parse_nsfw()
        self.assertFalse(js.entry.is_nsfw)


class JsonParserParseTest(unittest.TestCase):
    body = '<div>#<a href="#taktyk">taktyk</a> test text ' \
           '@<a href="@test_user">test_user</a> #<a href="#python">python</a></div>'

    def test_return_value(self):
        json_ = {}
        js = JsonParser(json_)
        self.assertEqual(js.entry, js.parse())

    def test_entry_values(self):
        json_ = {'id': 2137, 'type': 'entry', 'author': 'test_author', 'date': 'test_date',
                 'vote_count': 100, 'embed': {'url': 'someurl', 'plus18': True}, 'body': self.body}
        entry = JsonParser(json_).parse()
        self.assertEqual(2137, entry.id_)
        self.assertEqual('entry', entry.type_)
        self.assertEqual(None, entry.entry_id)
        self.assertEqual('test_author', entry.author)
        self.assertEqual('test_date', entry.date)
        self.assertEqual('100', entry.plus)
        self.assertEqual('someurl', entry.media_url)
        self.assertEqual(True, entry.is_nsfw)
        self.assertTrue('taktyk' in entry.tags)
        self.assertTrue('python' in entry.tags)


class HtmlParserTest(unittest.TestCase):
    entries = '''<html><body>
        <li class="entry iC "> <div class="wblock lcontrast dC  " data-id="1" data-type="entry"></div></li>
        <li class="entry iC "> <div class="wblock lcontrast dC  " data-id="2" data-type="entry"></div></li>
        <li class="entry iC "> <div class="wblock lcontrast dC  " data-id="3" data-type="entry"></div></li>
        </body></html>'''
    entry = '''<html><body>
        <li class="entry iC ">
         <div class="wblock lcontrast dC  " data-id="1" data-type="entry">
         <a class="color-1 showProfileSummary" href="https://www.wykop.pl/ludzie/test_user/" title=""><b>test_user</b></a>
         <time title="2018-05-05 21:36:47" pubdate=""></time><p class="vC" data-vc="1000" data-vcp="0" data-vcm="0">
         </p><div class="text"><p>Test text<a class="showSpoiler">pokaż spoiler</a>
        #<a class="showTagSummary" href="https://www.wykop.pl/tag/programowanie">programowanie</a>
        #<a class="showTagSummary" href="https://www.wykop.pl/tag/python">python</a></p>
         <div class="media-content" data-type="entry" data-id="1"><a href="https://www.test-url.pl/file.jpg"> </a>
        <span class="plus18item">18+</span></div></div></div>
         <ul>
         <li><div class="wblock lcontrast dC  " data-id="111" data-type="entrycomment">
         <a class="color-1 showProfileSummary" href="https://www.wykop.pl/ludzie/test_user_com1/" title=""><b>test_user_com1</b></a>
         <time title="2018-05-06 12:36:47" pubdate=""></time><p class="vC" data-vc="15" data-vcp="0" data-vcm="0">
         </p><div class="text"><p>Test text comment 1<a class="showSpoiler">pokaż spoiler</a></p>
         <div class="media-content" data-type="entry" data-id="1"><a href="https://www.test-url.pl/file2.jpg"> </a></div></div>
         </li>
         <li><div class="wblock lcontrast dC  " data-id="222" data-type="entrycomment">
         <a class="color-1 showProfileSummary" href="https://www.wykop.pl/ludzie/test_user_com2/" title=""><b>test_user_com2</b></a>
         <time title="2018-05-07 05:36:47" pubdate=""></time><p class="vC" data-vc="2" data-vcp="0" data-vcm="0">
         </p><div class="text"><p>Test text<a class="showSpoiler">pokaż spoiler</a>
        #<a class="showTagSummary" href="https://www.wykop.pl/tag/taktyk">taktyk</a></p>
         </div></ul></li></body></html>'''

    def test_find_ids_in_html(self):
        ids = HtmlParser.find_ids_in_html(self.entries)
        self.assertEqual(['1', '2', '3'], ids)

    def test_get_entries_soup_list(self):
        parser = HtmlParser('1', self.entry)
        self.assertEqual(3, len(parser.soup_list))

    def test_get_main_entry(self):
        entry = HtmlParser('1', self.entry).get_main_entry()
        self.assertEqual(1, entry.id_)
        self.assertEqual('test_user', entry.author)
        self.assertEqual('2018-05-05 21:36:47', entry.date)
        self.assertTrue('Test text' in entry.body)
        self.assertTrue('https://www.wykop.pl/tag/programowanie' in entry.body_html)
        self.assertEqual('1000', entry.plus)
        self.assertEqual('https://www.test-url.pl/file.jpg', entry.media_url)
        self.assertEqual(' programowanie python ', entry.tags)
        self.assertTrue(entry.is_nsfw)
        self.assertEqual('entry', entry.type_)
        self.assertIsNone(entry.entry_id)

    def test_get_comments_generator(self):
        comments = list(HtmlParser('1', self.entry).get_comments_generator(start_index=1))
        authors = ['test_user_com1', 'test_user_com2']
        self.assertEqual(2, len(comments))
        for i, com in enumerate(comments):
            self.assertEqual(authors[i], com.author)
            self.assertEqual('1', com.entry_id)
            self.assertEqual('entry_comment', com.type_)
