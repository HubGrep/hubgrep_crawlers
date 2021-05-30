import logging
import time
from urllib.parse import urljoin

from iso8601 import iso8601
from crawlers.lib.platforms.i_crawler import IResult, ICrawler

logger = logging.getLogger(__name__)

# https://developer.github.com/v3/search/


class GiteaResult(IResult):
    """
    {'id': 2,
    'owner': {'id': 5,
              'login': 'codi.cooperatiu',
              'full_name': '',
              'email': '',
              'avatar_url': 'http://gitea.codi.coop/avatars/a89a876bb0456b115c77dbee684d409b',
              'username': 'codi.cooperatiu'},
    'name': 'codi-theme',
    'full_name': 'codi.cooperatiu/codi-theme',
    'description': '',
    'empty': False,
    'private': False,
    'fork': False,
    'parent': None,
    'mirror': False,
    'size': 5188,
    'html_url': 'http://gitea.codi.coop/codi.cooperatiu/codi-theme',
    'ssh_url': 'root@gitea.codi.coop:codi.cooperatiu/codi-theme.git',
    'clone_url': 'http://gitea.codi.coop/codi.cooperatiu/codi-theme.git',
    'website': '',
    'stars_count': 0,
    'forks_count': 0,
    'watchers_count': 3,
    'open_issues_count': 0,
    'default_branch': 'master',
    'created_at': '2018-01-25T18:52:35Z',
    'updated_at': '2019-05-20T18:55:46Z',
    'permissions': {'admin': False,
                    'push': False,
                    'pull': True}}
    """

    def __init__(self, platform_id, search_result_item):
        name = search_result_item['name']
        owner_name = search_result_item['owner']['login']
        description = search_result_item['description'] or '?'
        last_commit = iso8601.parse_date(search_result_item['updated_at'])
        created_at = iso8601.parse_date(search_result_item['created_at'])
        language = None
        license_dict = search_result_item.get('license')
        license = license_dict.get('name', None) if license_dict else None

        html_url = search_result_item['html_url']

        super().__init__(platform_id=platform_id,
                         name=name,
                         description=description,
                         html_url=html_url,
                         owner_name=owner_name,
                         last_commit=last_commit,
                         created_at=created_at,
                         language=language,
                         license=license)


class GiteaCrawler(ICrawler):
    name = 'gitea'

    def __init__(self, id, base_url, state=None, auth_data=None, **kwargs):
        super().__init__(
            _id=id,
            base_url=base_url,
            path='api/v1/repos/search',
            state=state,
            auth_data=auth_data
        )
        self.request_url = urljoin(self.base_url, self.path)

    def crawl(self, state=None):
        if not state:
            page = 1
        else:
            page = state.get('page', False)
            if not page:
                logger.warning(f'{self} broken state, defaulting to start')
        results = True
        while results:
            params = dict(
                sort='created',
                limit=50,
                page=page
            )
            try:
                response = self.requests.get(self.request_url, params=params)
            except Exception as e:
                logger.error(e)
                return False, [], {}
            result = response.json()
            results = [GiteaResult(self._id, item)
                       for item in result['data']]
            state = {'page': page}
            yield True, results, state
            page += 1
            time.sleep(.5)
