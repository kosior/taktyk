import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.parsers import JsonParser


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
