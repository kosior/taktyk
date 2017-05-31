import logging
import os

from .. import auth, settings


def userkey_validator(userkey):
    if auth.is_key_valid(settings.APPKEY, userkey):
        logging.info('...klucz jest poprawny')
        return userkey
    else:
        raise ValueError('Niepoprawny lub nieaktualny klucz.')


def source_validator(source):
    if os.path.isfile(source):
        if is_text_file(source):
            return {'file': source}
        else:
            raise ValueError('Plik nie jest tekstowy.')
    elif os.path.isdir(source):
        if not os.listdir(source):
            raise ValueError('Folder jest pusty.')
        return {'dir': source}
    else:
        raise ValueError('Plik lub folder nie istnieje.')


def is_text_file(path):
    try:
        with open(path, 'rt') as file:
            file.readline()
    except (OSError, ValueError):
        return False
    else:
        return True


def ids_validator(ids):
    ids = ids.split(' ')
    f_ids = {id_ for id_ in ids if id_.isdigit()}
    if not f_ids:
        raise ValueError('Brak odpowiednich id wpisów.')
    return f_ids
