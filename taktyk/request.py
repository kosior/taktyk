import logging
import traceback
from json.decoder import JSONDecodeError

try:
    import requests
except ImportError:
    logging.debug('ImportError - requests - ' + __file__)


class Request:
    @classmethod
    def get(cls, url, exit_=False, msg=None, **kwargs):
        try:
            response = requests.get(url, **kwargs)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            logging.critical('Brak połączenia z internetem')
            raise SystemExit
        except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as err:
            logging.debug(url)
            logging.debug(traceback.format_exc())
            if msg:
                logging.error(msg)
            if exit_:
                logging.error(err)
                raise SystemExit
            else:
                return None
        else:
            return response

    @classmethod
    def get_json(cls, url, exit_=False, msg=None, **kwargs):
        request = cls.get(url, exit_=exit_, msg=msg, **kwargs)
        try:
            json_ = request.json()
        except (TypeError, AttributeError, JSONDecodeError) as err:
            logging.debug(url)
            logging.debug(traceback.format_exc())
            if msg:
                logging.error(msg)
            if exit_:
                logging.error(err)
                raise SystemExit
            else:
                raise ValueError
        else:
            if isinstance(json_, dict) and (json_.get('error') or not json_):
                error_info = json_.get('error')
                logging.debug(error_info)
                raise ValueError(error_info)
            elif isinstance(json_, list) and not json_:
                raise ValueError('Empty list')
            return json_
