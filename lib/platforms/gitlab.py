import logging
import time
from urllib.parse import urljoin

import requests
from iso8601 import iso8601
from lib.platforms._generic import GenericResult, GenericIndexer

logger = logging.getLogger(__name__)


class GitLabResult(GenericResult):
    """
    {'id': 1241825,
     'description': 'Pacote LaTeXe para produção de monografias, dissertações e teses',
     'name': 'ufrrj',
     'name_with_namespace': 'Alessandro Duarte / ufrrj',
     'path': 'ufrrj',
     'path_with_namespace': 'dedekindbr/ufrrj',
     'created_at': '2016-05-30T04:27:14.463Z',
     'default_branch': 'master',
     'tag_list': [],
     'ssh_url_to_repo': 'git@gitlab.com:dedekindbr/ufrrj.git',
     'http_url_to_repo': 'https://gitlab.com/dedekindbr/ufrrj.git',
     'web_url': 'https://gitlab.com/dedekindbr/ufrrj',
     'readme_url': 'https://gitlab.com/dedekindbr/ufrrj/-/blob/master/README.md',
     'avatar_url': None,
     'forks_count': 0,
     'star_count': 0,
     'last_activity_at': '2016-05-30T04:27:15.194Z',
     'namespace': {'id': 502506,
                   'name': 'Alessandro Duarte',
                   'path': 'dedekindbr',
                   'kind': 'user',
                   'full_path': 'dedekindbr',
                   'parent_id': None,
                   'avatar_url': 'https://secure.gravatar.com/avatar/ec3a8f5183465a232283493f3de0a80d?s=80&d=identicon',
                   'web_url': 'https://gitlab.com/dedekindbr'}}
    """
    def __init__(self, platform_id, search_result_item):
        name = search_result_item['name']
        owner_name = search_result_item['namespace']['path']
        description = search_result_item['description'] or ''
        last_commit = iso8601.parse_date(
            search_result_item['last_activity_at'])
        created_at = iso8601.parse_date(search_result_item['created_at'])
        language = None
        license = None

        html_url = search_result_item['http_url_to_repo']

        super().__init__(platform_id=platform_id,
                         name=name,
                         description=description,
                         html_url=html_url,
                         owner_name=owner_name,
                         last_commit=last_commit,
                         created_at=created_at,
                         language=language,
                         license=license)


class GitLabIndexer(GenericIndexer):
    name = 'gitlab'

    # https://docs.gitlab.com/ee/api/projects.html

    def __init__(self, id, base_url, state=None, auth_data=None, **kwargs):
        super().__init__(
            _id=id,
            base_url=base_url,
            path='/api/v4/projects',
            state=state,
            auth_data=auth_data
        )
        self.request_url = urljoin(self.base_url, self.path)

    def crawl(self, state=None):
        url = False
        if state:
            url = state.get('url', False)
            if not url:
                logger.warning('{self} broken state, defaulting to start')

        if not url:
            url = '/api/v4/projects?pagination=keyset&per_page=100&order_by=id&sort=desc'

        while url:
            try:
                response = self.requests.get(urljoin(self.base_url, url))
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.error(e)
                logger.error(e.response.reason)
                logger.error(e.response.text)
                return False, [], {}
            project_page = response.json()
            repos = [GitLabResult(self._id, result) for result in project_page]
            state = {'url': url}
            yield True, repos, state

            # https://stackoverflow.com/questions/32312758/python-requests-link-headers
            header_next = response.links.get('next', {})
            url = header_next.get('url', False)
            if not url:
                # not hit rate limit, and we dont have a next url - finished!
                # reset state
                yield True, [], None
            time.sleep(.1)
