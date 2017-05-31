import getpass
import hashlib
import json
import logging
import os
import traceback
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError

try:
    import bs4
    import requests
except ImportError:
    logging.debug('ImportError - bs4, requests - ' + __file__)

from . import settings


def get_username():
    if not settings.USERNAME:
        username = input('Podaj login: ')
        settings.USERNAME = username
    return settings.USERNAME


def log_in_for_userkey():
    headers = {}
    url = settings.API_LOGIN_URL + settings.APPKEY

    while True:
        username = get_username()

        if settings.SECRETKEY and settings.ACCOUNTKEY:
            data = {'login': username, 'accountkey': settings.ACCOUNTKEY}
            headers = apisign(url, settings.SECRETKEY, **data)
            msg = 'Nieprawidłowy login, accountkey, lub secretkey.'
        else:
            print('--- Ctrl+C aby wyjść ---')
            password = getpass.getpass(prompt='Podaj hasło: ', stream=None)
            data = {'login': username, 'password': password}
            msg = 'Nieprawidłowy login lub hasło.'

        response = requests.post(url, data=data, headers=headers)

        password = None
        data = None

        try:
            userkey = response.json()['userkey']
        except (json.decoder.JSONDecodeError, KeyError):
            logging.error(msg)
            logging.info(traceback.format_exc())
            continue
        else:
            settings.USERKEY = userkey
            save_userkey(userkey)
            break


def get_token():
    login_url = settings.LOGIN_URL
    login_page = requests.get(login_url)
    try:
        login_page_soup = bs4.BeautifulSoup(login_page.text, 'html.parser')
        token_ = login_page_soup.find(id='__token')
        return token_.get('value')
    except AttributeError as err:
        logging.critical('Token nie odnaleziony')
        logging.debug(err)
        raise SystemExit


def log_in_for_session():
    token = get_token()
    login_url = settings.LOGIN_URL
    wykop_url = settings.WYKOP_URL

    while True:
        print('--- Ctrl+C aby wyjść ---')
        username = get_username()
        password = getpass.getpass(prompt='Podaj hasło: ', stream=None)

        session = requests.session()
        session.post(login_url, data={'user[username]': username,
                                      'user[password]': password,
                                      '__token': token})

        password = None

        # checking if logged correctly
        main_page = session.get(wykop_url)
        soup = bs4.BeautifulSoup(main_page.text, 'html.parser')
        try:
            username_logged = soup.find(class_='avatar').get('alt')
        except AttributeError:
            logging.error('Błąd przy logowaniu.')
            continue
        else:
            if username_logged.lower() == username.lower():
                return session
            else:
                logging.error('Nieprawidłowy login lub hasło.')
                continue


def set_userkey():
    if settings.USERKEY:
        if is_key_valid(settings.APPKEY, settings.USERKEY):
            return True
        else:
            logging.critical('Nieprawidłowy lub przeterminowany userkey.')
            raise SystemExit
    else:
        userkey = get_and_check_saved_userkey()
        if userkey:
            settings.USERKEY = userkey
        else:
            log_in_for_userkey()


def save_userkey(userkey):
    path = os.path.join(settings.USER_FILES_PATH, settings.USERKEY_FILE)
    data = {
        'userkey': userkey,
        'expire': '{}'.format(datetime.now() + timedelta(hours=23))
    }
    with open(path, 'w') as file:
        json.dump(data, file)


def get_saved_userkey_from_file():
    path = os.path.join(settings.USER_FILES_PATH, settings.USERKEY_FILE)
    try:
        with open(path, 'r') as file:
            try:
                return json.load(file)
            except JSONDecodeError:
                return
    except FileNotFoundError:
        return {}


def get_and_check_saved_userkey():
    userkey_info = get_saved_userkey_from_file()
    userkey = userkey_info.get('userkey')
    expiration_date = userkey_info.get('expire')
    if userkey and expiration_date:
        expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d %H:%M:%S.%f')
        if datetime.now() > expiration_date:
            return False
        return userkey
    return False


def is_key_valid(appkey, userkey=None):
    url = settings.API_CHECK_URL + appkey

    if userkey:
        url += '/userkey/' + userkey

    if 'error' in requests.get(url, headers=apisign(url, settings.SECRETKEY)).text:
        return False
    return True


def apisign(url_, secret=None, **post_kwargs):
    if secret:
        post = [post_kwargs.get(key) for key in sorted(post_kwargs.keys())]
        post = ','.join(post)
        post = post.encode()
        url_ = url_.encode()
        secret = secret.encode()
        m = hashlib.md5()
        m.update(secret + url_ + post)
        return {'apisign': m.hexdigest()}
    return {}
