""" All crawlers share this interface to work with our crawler API/CLI. """
import requests
from typing import List, Tuple
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from crawlers.lib.serializable import Serializable


class LEGACY_IResult(Serializable):
    def __init__(
            self,
            name,
            description,
            html_url,
            owner_name,
            last_commit,
            created_at,
            platform_id,
            language=None,
            license=None):
        super().__init__()
        self.name = name
        self.description = description
        self.html_url = html_url
        self.owner_name = owner_name
        self.last_commit = last_commit
        self.created_at = created_at
        self.language = language
        self.license = license
        self.platform_id = platform_id

    def save(db, commit=True):
        pass

    def __str__(self):
        return f'<{self.owner_name} / {self.name} @ {self.platform_id}>'


class IResult(Serializable):
    def __init__(
            self,
            name,
            description,
            html_url,
            owner_name,
            last_commit,
            created_at,
            platform_id,
            language=None,
            license=None):
        super().__init__()
        self.name = name
        self.description = description
        self.html_url = html_url
        self.owner_name = owner_name
        self.last_commit = last_commit
        self.created_at = created_at
        self.language = language
        self.license = license
        self.platform_id = platform_id

    def save(db, commit=True):
        pass

    def __str__(self):
        return f'<{self.owner_name} / {self.name} @ {self.platform_id}>'


class ICrawler:
    name = None

    def __init__(self, _id, type, base_url, path, state, auth_data=None, user_agent=None):
        self._id = _id
        self.type = type
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

    def crawl(self, state: dict) -> Tuple[bool, List[IResult], dict]:
        raise NotImplementedError


