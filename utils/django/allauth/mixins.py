# -*- coding: utf-8 -*-
import threading

import requests
from urllib3.util.retry import Retry

from utils.requests import TimeoutHTTPAdapter

local = threading.local()


class SessionAdapterMixin(object):

    def get_session(self):
        name = f'{self.__class__.__name__.lower()}_session'
        session = getattr(local, name, None)
        if session:
            return session

        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        session = requests.Session()
        adapter = TimeoutHTTPAdapter(timeout=3, max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        setattr(local, name, session)
        return session
