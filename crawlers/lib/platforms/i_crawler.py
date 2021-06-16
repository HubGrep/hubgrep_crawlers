""" All crawlers share this interface to work with our crawler API/CLI. """
import requests
from typing import List, Tuple
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class ICrawler:
    name = None

    def __init__(self, base_url, path, state, auth_data=None, user_agent=None):
        self.base_url = base_url
        self.path = path
        self.auth_data = auth_data
        self.state = state

        self.requests = requests.session()
        retries = Retry(total=3,
                        backoff_factor=10,
                        status_forcelist=[429, 500, 502, 503, 504])
        self.requests.mount("https://", HTTPAdapter(max_retries=retries))
        if user_agent is not None:
            self.requests.headers.update({"user-agent": user_agent})

    def __str__(self):
        return f'<{self.name}@{self.base_url}>'

    @staticmethod
    def state_from_job_data(job_data: dict) -> dict:
        return job_data  # override this function for specific pre-processing in specific crawlers

    def crawl(self, state: dict) -> Tuple[bool, List[dict], dict]:
        """ :return: success, repos, state """
        raise NotImplementedError


