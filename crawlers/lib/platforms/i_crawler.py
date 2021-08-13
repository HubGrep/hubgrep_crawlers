""" All crawlers share this interface to work with our crawler API/CLI. """
import logging
import math
import requests
import time
from urllib.parse import urljoin
from typing import List, Tuple, Union
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from crawlers.constants import CRAWLER_DEFAULT_THROTTLE, BLOCK_KEY_FROM_ID, BLOCK_KEY_TO_ID

logger = logging.getLogger(__name__)


class ICrawler:
    type: str = None

    def __init__(self, base_url, path, state, api_key=None, user_agent=None, extra_headers: dict = {}):
        self.base_url = base_url
        self.path = path
        self.api_key = api_key
        self.state = state
        self.extra_headers = extra_headers

        self.crawl_url = urljoin(self.base_url, self.path)

        self.requests = requests.session()
        self.requests.headers.update(self.extra_headers)
        retries = Retry(total=3,
                        backoff_factor=10,
                        status_forcelist=[429, 500, 502, 503, 504])
        self.requests.mount("https://", HTTPAdapter(max_retries=retries))
        if user_agent is not None:
            self.requests.headers.update({"User-Agent": user_agent})

    def __str__(self):
        return f'<{self.type}@{self.base_url}>'

    def handle_ratelimit(self, response=None):
        logger.debug(f"default throttling - sleep for {CRAWLER_DEFAULT_THROTTLE}")
        time.sleep(CRAWLER_DEFAULT_THROTTLE)

    def crawl(self, state: dict = None) -> Tuple[bool, List[dict], dict]:
        """ :return: success, repos, state, Exception (if any) """
        raise NotImplementedError

    @staticmethod
    def state_from_block_data(block_data: dict) -> dict:
        return block_data  # override this function for specific crawler pre-processing

    @classmethod
    def set_state(cls, state: dict = None) -> dict:
        """
        Init and update state between each query, based on ascending pagination.
        """
        if not state:
            state = {}
        state['per_page'] = state.get('per_page', 100)
        state['is_done'] = state.get('is_done', False)

        # set the current page
        if not state.get('page', False):
            if state.get(BLOCK_KEY_FROM_ID, False):
                state['page'] = math.ceil(
                    state[BLOCK_KEY_FROM_ID] / state['per_page'])
            else:
                state['page'] = 1  # start at the beginning
        else:
            state['page'] += 1  # set next

        # calculate the last page for this block
        if not state.get('page_end', False):
            if state.get(BLOCK_KEY_TO_ID, False):
                state['page_end'] = math.ceil(
                    state[BLOCK_KEY_TO_ID] / state['per_page'])  # last inclusive page
            else:
                state['page_end'] = -1  # no limit

        return state

    @classmethod
    def has_next_crawl(cls, state: dict) -> bool:
        """
        Decide if there are more repositories to crawl for, within current block.
        """
        is_in_page_range = state['page'] <= state['page_end']
        return not state['is_done'] and (state['page_end'] == -1 or is_in_page_range)
