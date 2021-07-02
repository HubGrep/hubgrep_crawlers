import logging
import time
from typing import List, Tuple
from urllib.parse import urljoin

from crawlers.constants import GITLAB_PER_PAGE_MAX
from crawlers.lib.platforms.i_crawler import ICrawler

logger = logging.getLogger(__name__)

class GitLabCrawler(ICrawler):
    name = 'gitlab'

    # https://docs.gitlab.com/ee/api/projects.html

    def __init__(self, base_url, state=None, auth_data=None, user_agent=None, **kwargs):
        super().__init__(
            base_url=base_url,
            path='/api/v4/projects',
            state=self.set_state(state),
            auth_data=auth_data,
            user_agent=user_agent
        )
        self.request_url = urljoin(self.base_url, self.path)
        if auth_data:
            self.requests.headers.update({"PRIVATE-TOKEN": auth_data['PRIVATE-TOKEN']})

    @classmethod
    def set_state(cls, state: dict = None) -> dict:
        state["per_page"] = state.get("per_page", GITLAB_PER_PAGE_MAX)
        state = super().set_state(state)
        return state

    def handle_ratelimit(self, response = None):
        if response:
            remaining = int(response.headers.get("RateLimit-Remaining", -1))
            reset_ts = int(response.headers.get("RateLimit-Reset", -1))
            if remaining == -1 or reset_ts == -1:
                logger.warning("no ratelimit found in gitlab response headers")
                super().handle_ratelimit(response)
            elif remaining == 0:
                # otherwise spam&sleep
                sleep_s = reset_ts - time.time()
                logger.info(f"ratelimit exceeded for {self}, sleeping for {sleep_s} seconds...")
                time.sleep(sleep_s)
        else:
            super().handle_ratelimit()

    def crawl(self, state: dict = None) -> Tuple[bool, List[dict], dict]:
        """ :return: success, repos, state """
        state = state or self.state
        while self.has_next_crawl(state):
            params = dict(
                order_by="id",
                page=state["page"],
                per_page=state['per_page'],
                sort='asc'
            )
            try:
                response = self.requests.get(self.request_url, params=params)
                if not response.ok:
                    logger.warning(f"(skipping block chunk) gitlab - {self.base_url} " +
                                   f"- response not ok, status: {response.status_code}")
                    logger.warning(response.headers.__dict__)
                    return False, [], state  # nr.1 - we skip rest of this block, hope we get it next time
                repos = response.json()
            except Exception as e:
                logger.exception(f"(skipping block chunk) gitlab crawler crashed")
                return False, [], state  # nr.2 - we skip rest of this block, hope we get it next time

            state['is_done'] = len(repos) != state['per_page']  # finish early, we reached the end

            yield True, repos, state
            self.handle_ratelimit(response)
            state = self.set_state(state)

        """ expected GitLab result
        {
            'id': 1241825,
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
                          'web_url': 'https://gitlab.com/dedekindbr'}
        }
        """
