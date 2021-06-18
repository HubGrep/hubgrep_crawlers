import logging
import math
from typing import List, Tuple
from urllib.parse import urljoin
from iso8601 import iso8601

from crawlers.constants import JOB_TO_ID, JOB_FROM_ID
from crawlers.lib.platforms.i_crawler import ICrawler

logger = logging.getLogger(__name__)


class GiteaResult:
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

    def __init__(self, search_result_item):
        name = search_result_item['name']
        owner_name = search_result_item['owner']['login']
        description = search_result_item['description'] or '?'
        last_commit = iso8601.parse_date(search_result_item['updated_at'])
        created_at = iso8601.parse_date(search_result_item['created_at'])
        language = None
        license_dict = search_result_item.get('license')
        license = license_dict.get('name', None) if license_dict else None

        html_url = search_result_item['html_url']

        super().__init__(name=name,
                         description=description,
                         html_url=html_url,
                         owner_name=owner_name,
                         last_commit=last_commit,
                         created_at=created_at,
                         language=language,
                         license=license)


class GiteaCrawler(ICrawler):
    name = 'gitea'

    def __init__(self, base_url, state=None, auth_data=None, user_agent=None, **kwargs):
        super().__init__(
            base_url=base_url,
            path='api/v1/repos/search',
            state=self.set_state(state),
            auth_data=auth_data,
            user_agent=user_agent
        )
        self.request_url = urljoin(self.base_url, self.path)

    @staticmethod
    def set_state(state: dict = None) -> dict:
        """
        Init and update state between each query.
        """
        if not state:
            state = {}
        state['per_page'] = state.get('per_page', 50)
        state['is_done'] = state.get('per_page', False)

        if not state.get('page', False):
            if state.get(JOB_FROM_ID, False):
                state['page'] = math.ceil(state[JOB_FROM_ID] / state['per_page'])
            else:
                state['page'] = 1  # start at the beginning
        else:
            state['page'] += 1  # set next

        if not state.get('page_end', False):
            if state.get(JOB_TO_ID, False):
                state['page_end'] = math.ceil(state[JOB_TO_ID] / state['per_page'])
            else:
                state['page_end'] = -1  # no limit

        return state

    @staticmethod
    def has_next_crawl(state: dict) -> bool:
        """ Decide if there are more repositories to crawl for, within current job. """
        return not state['is_done'] and (state['page_end'] == -1 or state['page'] < state['page_end'])

    def crawl(self, state: dict = None) -> Tuple[bool, List[GiteaResult], dict]:
        state = state or self.state
        while self.has_next_crawl(state):
            params = dict(
                sort='created',
                limit=state['per_page'],
                page=state["page"]
            )
            try:
                response = self.requests.get(self.request_url, params=params)
                result = response.json()
            except Exception as e:
                logger.error(e)
                return False, [], state

            state['is_done'] = len(result['data']) != state['per_page']

            yield True, result['data'], state
            self.handle_ratelimit(response)
            state = self.set_state(state)
