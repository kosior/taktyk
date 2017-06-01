import argparse
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk.args import _parse, get_commands, prepare_static_args


class ParseTest(unittest.TestCase):
    args = [('ModulesHandler', True),
            ('Configure', True),
            ('nsfw', False),
            ('CreateFolders', True),
            ('CheckForUpdate', True),
            ('update', False),
            ('new', False),
            ('pdk', False),
            ('file', False),
            ('ids', False),
            ('selenium', None),
            ('session', False),
            ('delete', None),
            ('skip', False),
            ('scrape', False),
            ('DBHandler', True),
            ('html', False),
            ('save', False),
            ('comments', False)]

    def test_default_args(self):
        parsed = _parse(static_args=[])
        for arg in self.args:
            key, value = arg
            self.assertEqual(parsed[key], value)

    def test_order(self):
        parsed = _parse(static_args=[])
        parsed_args_name_list = list(parsed.keys())
        prev = -1

        for arg_name, _ in self.args:
            next_ = parsed_args_name_list.index(arg_name)
            self.assertTrue(next_ > prev)
            prev = next_

    def test_nsfw_arg(self):
        parsed = _parse(static_args=['-n'])
        self.assertEqual(parsed['nsfw'], True)
        parsed = _parse(static_args=['--nsfw'])
        self.assertEqual(parsed['nsfw'], True)

    def test_update_arg(self):
        parsed = _parse(static_args=['-u'])
        self.assertEqual(parsed['update'], True)
        parsed = _parse(static_args=['--update'])
        self.assertEqual(parsed['update'], True)

    def test_new_arg(self):
        parsed = _parse(static_args=['--new'])
        self.assertEqual(parsed['new'], True)

    def test_pdk_arg(self):
        parsed = _parse(static_args=['-p'])
        self.assertEqual(parsed['pdk'], True)
        parsed = _parse(static_args=['--pdk'])
        self.assertEqual(parsed['pdk'], True)

    def test_file_arg(self):
        parsed = _parse(static_args=['-f'])
        self.assertEqual(parsed['file'], True)
        parsed = _parse(static_args=['--file'])
        self.assertEqual(parsed['file'], True)

    def test_ids_arg(self):
        parsed = _parse(static_args=['-i'])
        self.assertEqual(parsed['ids'], True)
        parsed = _parse(static_args=['--ids'])
        self.assertEqual(parsed['ids'], True)

    def test_selenium_arg_without_choice(self):
        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError):
                _parse(static_args=['-s'])

    def test_selenium_arg_wrong_choice(self):
        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError):
                _parse(static_args=['-s', 'mistake'])

    def test_selenium_arg_chrome(self):
        parsed = _parse(static_args=['-s', 'chrome'])
        self.assertEqual(parsed['selenium'], 'chrome')

    def test_selenium_arg_firefox(self):
        parsed = _parse(static_args=['-s', 'firefox'])
        self.assertEqual(parsed['selenium'], 'firefox')

    def test_session_arg(self):
        parsed = _parse(static_args=['-S'])
        self.assertEqual(parsed['session'], True)
        parsed = _parse(static_args=['--session'])
        self.assertEqual(parsed['session'], True)

    def test_delete_arg_without_choice(self):
        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError):
                _parse(static_args=['-d'])

    def test_delete_arg_wrong_choice(self):
        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError):
                _parse(static_args=['-d', 'mistake'])

    def test_delete_arg_db(self):
        parsed = _parse(static_args=['-d', 'db'])
        self.assertEqual(parsed['delete'], 'db')

    def test_delete_arg_wykop(self):
        parsed = _parse(static_args=['-d', 'wykop'])
        self.assertEqual(parsed['delete'], 'wykop')

    def test_delete_arg_all(self):
        parsed = _parse(static_args=['-d', 'all'])
        self.assertEqual(parsed['delete'], 'all')

    def test_skip_arg(self):
        parsed = _parse(static_args=['--skip'])
        self.assertEqual(parsed['skip'], True)

    def test_scrape_arg(self):
        parsed = _parse(static_args=['--scrape'])
        self.assertEqual(parsed['scrape'], True)

    def test_html_arg(self):
        parsed = _parse(static_args=['--html'])
        self.assertEqual(parsed['html'], True)

    def test_html_arg_with_optional_tag(self):
        parsed = _parse(static_args=['--html', 'sometag'])
        self.assertEqual(parsed['html'], 'sometag')

    def test_save_arg(self):
        parsed = _parse(static_args=['--save'])
        self.assertEqual(parsed['save'], True)

    def test_comments_arg(self):
        parsed = _parse(static_args=['-c'])
        self.assertEqual(parsed['comments'], True)
        parsed = _parse(static_args=['--comments'])
        self.assertEqual(parsed['comments'], True)

    def test_mutually_exclusive_group(self):
        group_args = [['--update'], ['--file'], ['--ids'], ['--selenium', 'firefox'], ['--session'],
                      ['--delete'], ['--html'], ['--save'], ['--comments']]
        for arg1 in group_args:
            group_args_copy = group_args.copy()
            group_args_copy.remove(arg1)
            for arg2 in group_args_copy:
                with self.assertRaises(SystemExit):
                    with self.assertRaises(argparse.ArgumentError):
                        _parse(static_args=[*arg1, *arg2])


class GetCommandsTest(unittest.TestCase):
    def test_if_return_dict(self):
        self.assertIsInstance(get_commands(), dict)

    def test_names_in_commands(self):
        args = [key for key in _parse(static_args=[]).keys()]
        commands = get_commands()
        for arg in args:
            self.assertEqual(arg, commands[arg].name)

    def test_if_execute_exist_in_commands(self):
        args = [key for key in _parse(static_args=[]).keys()]
        commands = get_commands()
        for arg in args:
            self.assertTrue('execute' in commands[arg].__dict__.keys())


class PrepareStaticArgsTest(unittest.TestCase):
    def setUp(self):
        self.sa = sys.argv[1:]

    def test_when_static_args_is_none(self):
        self.assertEqual(self.sa, prepare_static_args(None))

    def test_filter_empty_strings(self):
        self.assertEqual(self.sa, prepare_static_args(['', '', '']))

    def test_if_static_args_are_added(self):
        self.sa.extend(['-s', 'chrome', '--scrape'])
        self.assertEqual(self.sa, prepare_static_args(['-s', 'chrome', '--scrape']))

    def test_if_duplicates_are_removed(self):
        self.sa.extend(['-i', '--scrape', '-n'])
        self.assertEqual(self.sa, prepare_static_args(['-i', '--scrape', '-n', '-n', '-i']))
