import argparse
import logging
import sys
from collections import OrderedDict
from inspect import getmembers, isclass

from .commands import abs_base, script_commands, user_commands


class OrderedNamespace(argparse.Namespace):
    def __init__(self, **kwargs):
        self.__dict__['ordered'] = OrderedDict()
        super().__init__(**kwargs)

    def __setattr__(self, key, value):
        self.__dict__['ordered'][key] = value
        super().__setattr__(key, value)


def _parse(static_args=None):
    """Argument order matters. Arguments will be processed from top to bottom"""
    parser = argparse.ArgumentParser(prog='Taktyk')
    group = parser.add_mutually_exclusive_group()

    parser.add_argument('--ModulesHandler', help=argparse.SUPPRESS, default=True)
    parser.add_argument('--Configure', help=argparse.SUPPRESS, default=True)
    parser.add_argument('-n', '--nsfw', help='włącz ignorowanie wpisów nsfw', action='store_true')
    parser.add_argument('--CreateFolders', help=argparse.SUPPRESS, default=True)
    parser.add_argument('--CheckForUpdate', help=argparse.SUPPRESS, default=True)
    group.add_argument('-u', '--update', help='aktualizacja programu', action='store_true')

    parser.add_argument('--new', help='utwórz nową bazę danych', action='store_true')
    parser.add_argument('-p', '--pdk', help='podaj userkey', action='store_true')

    group.add_argument('-f', '--file', help='podaj ścieżkę do pliku tekstowego lub folderu',
                       action='store_true')
    group.add_argument('-i', '--ids', help='podaj numery wpisów', action='store_true')
    group.add_argument('-s', '--selenium', help='użyj selenium, aby pobrać numery wpisów',
                       choices=['firefox', 'chrome'])
    group.add_argument('-S', '--session', help='użyj requests.Session, aby pobrać numery wpisów',
                       action='store_true')
    group.add_argument('-d', '--delete', help='usuwanie wpisów z wybranego zasięgu',
                       choices=['db', 'wykop', 'all'])

    parser.add_argument('--skip', help='pomiń pobieranie plików', action='store_true')
    parser.add_argument('--scrape', help='włącz tryb scrapowania', action='store_true')
    parser.add_argument('--DBHandler', help=argparse.SUPPRESS, default=True)

    group.add_argument('--html', help='utwórz ponownie plik html', action='store_true')
    group.add_argument('--save', help='pobierz pliki z wpisów z bazy danych', action='store_true')
    group.add_argument('-c', '--comments', help='zaktualizuj komentarze we wpisach',
                       action='store_true')

    args = parser.parse_args(static_args, OrderedNamespace())
    return args.ordered


def get_commands():
    commands = []
    for module_name in (script_commands, user_commands):
        commands.extend(getmembers(module_name,
                                   lambda x: isclass(x) and issubclass(x, abs_base.AbsCommand)))
    commands = {value.name: value for _, value in commands}
    return commands


def process_args(static_args=None):
    args = sys.argv[1:]
    if static_args:
        logging.info('...podane argumenty: %s', static_args)
        args.extend(static_args)
        args = list(set(args))

    logging.info('...konfiguracja i przetwarzanie argumentów')

    parsed_args = _parse(args)
    commands = get_commands()

    for arg_key, arg_value in parsed_args.items():
        if arg_value:
            command_class = commands.get(arg_key, abs_base.NoCommand)
            command_class().execute(arg_value)
