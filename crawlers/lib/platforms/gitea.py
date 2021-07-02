import logging
from typing import List, Tuple
from urllib.parse import urljoin

from crawlers.constants import GITEA_PER_PAGE_MAX
from crawlers.lib.platforms.i_crawler import ICrawler

logger = logging.getLogger(__name__)


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

    @classmethod
    def set_state(cls, state: dict = None) -> dict:
        state["per_page"] = state.get("per_page", GITEA_PER_PAGE_MAX)
        state = super().set_state(state)
        return state

    def crawl(self, state: dict = None) -> Tuple[bool, List[dict], dict]:
        state = state or self.state
        while self.has_next_crawl(state):
            params = dict(
                sort='created',
                limit=state['per_page'],
                page=state["page"]
            )
            try:
                response = self.requests.get(self.request_url, params=params)
                if not response.ok:
                    return False, [], state  # nr.1 - we skip rest of this block, hope we get it next time
                result = response.json()
            except Exception as e:
                logger.error(e)
                return False, [], state  # nr.2 - we skip rest of this block, hope we get it next time

            state['is_done'] = len(result['data']) != state['per_page']  # finish early, we reached the end

            yield True, result['data'], state
            self.handle_ratelimit(response)
            state = self.set_state(state)

        """ expected Gitea result
        {
            'id': 2,
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
                            'pull': True}
        }
        """
