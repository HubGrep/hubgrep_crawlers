import requests
from datetime import datetime
from urllib.parse import urljoin


class GenericResult:
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
        return f'<{self.owner_name}/{self.name} @ {self.platform_id}>'


class GenericCrawler:
    def __init__(self, _id, base_url, path, state, auth_data=None):
        self._id = _id
        self.base_url = base_url
        self.path = path
        self.auth_data = auth_data
        self.state = state
        self.requests = requests.session()

    def __str__(self):
        return f'<{self.name}@{self.base_url}>'
