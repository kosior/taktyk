import os


USERNAME = None
PASSWORD = None

APPKEY = None
SECRETKEY = None
ACCOUNTKEY = None
USERKEY = None

STATIC_ARGS = []  # here you can set default args e.g. ['-s', 'chrome', '--skip']

# files with this exts will be downloaded (.webm for gfycat)
EXTS = []  # will be set by utils.ConfigFile. Default exts: ['.gif', '.jpg', '.jpeg', '.png', '.webm']

DB_NAME = 'taktyk.db'
TEMPLATE_NAME = 'template.html'
USERKEY_FILE = 'userkey.txt'
CONFIG_FILE = 'config.ini'

# URLS (here are all urls used in this script):
# used in auth.py:
WYKOP_URL = 'https://www.wykop.pl'
API_WYKOP_URL = 'https://a.wykop.pl'
LOGIN_URL = 'https://www.wykop.pl/zaloguj/'
API_LOGIN_URL = 'https://a.wykop.pl/user/login/appkey/'
API_CHECK_URL = 'https://a.wykop.pl/appkey/'
# ---

FAVORITES_URL_F = 'https://www.wykop.pl/i/ludzie/ulubione/{username}/entries/strona/'
ENTRY_URL = 'https://www.wykop.pl/wpis/'
ENTRY_URL_SCRAPE = 'https://www.wykop.pl/i/wpis/'

API_FAVORITES_URL_F = 'https://a.wykop.pl/favorites/entries/userkey/{userkey}/appkey/{appkey}/page/'
API_ENTRY_URL_F = 'https://a.wykop.pl/entries/index/{{index}}/appkey/{appkey}'
API_UNFAV_URL_F = 'https://a.wykop.pl/entries/favorite/{{id}}/userkey/{userkey}/appkey/{appkey}'

CHROME_DRIVER_URL = 'https://chromedriver.storage.googleapis.com'
FIREFOX_DRIVER_URL = 'https://github.com/mozilla/geckodriver/releases'

SELENIUM_DRIVER_URLS = {
    'chrome': 'https://chromedriver.storage.googleapis.com',
    'firefox': 'https://github.com/mozilla/geckodriver/releases'
}

GITHUB_MASTER_ZIP_URL = 'https://github.com/kosior/taktyk/archive/master.zip'
GITHUB_LATEST_RELEASE_URL = 'https://github.com/kosior/taktyk/releases/latest'
GFYCAT_API = 'https://gfycat.com/cajax/get/'

# Directories:
USER_DIR_NAME = 'wykopTAKTYK'
DB_DIR_NAME = 'db'
FILES_DIR_NAME = 'pliki'
COMMENTS_DIR_NAME = 'komentarze'
NSFW_DIR_NAME = 'nsfw'
SELENIUM_DRIVER_DIR_NAME = 'seleniumdrivers'
TEMPLATE_DIR_NAME = 'templates'

# Paths:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
USER_FILES_PATH = os.path.join(SAVE_PATH, USER_DIR_NAME)
TEMPLATES_PATH = os.path.join(BASE_DIR, TEMPLATE_DIR_NAME)
SELENIUM_DRIVER_PATH = None

# Used modules:
# [import_name, install_name, version]
MODULES = [
    ['requests', 'requests', '2.18.1'],
    ['bs4', 'beautifulsoup4', '4.6.0'],
    ['jinja2', 'jinja2', '2.9.6'],
    ['selenium', 'selenium', '3.4.3']
]

# Other:
STRATEGY = None
METHOD = None
SOURCE = {}
SCRAPE = False
FULL_UPDATE = False
SKIP_FILES = False
BROWSER = None
NSFW_FILTER = False
DB_IDS = []

# for tracking how many entries and comments were added:
ENTRIES_ADDED = 0
COMMENTS_ADDED = 0
# ---

APPKEY = APPKEY if APPKEY else 'aNd401dAPp'


def dirs_to_create():
    return [
        [DB_DIR_NAME],
        [FILES_DIR_NAME, COMMENTS_DIR_NAME],
        [FILES_DIR_NAME, NSFW_DIR_NAME, COMMENTS_DIR_NAME] if not NSFW_FILTER else []
    ]
