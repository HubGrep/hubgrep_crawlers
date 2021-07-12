import logging
from functools import reduce
from typing import List, Tuple
from urllib.parse import urljoin

from crawlers.constants import GITEA_PER_PAGE_MAX, GITEA_REPO_TOPICS_KEY
from crawlers.lib.platforms.i_crawler import ICrawler

logger = logging.getLogger(__name__)


class GiteaCrawler(ICrawler):
    name = "gitea"

    def __init__(self, base_url, state=None, auth_data=None, user_agent=None):
        super().__init__(
            base_url=base_url,
            path="api/v1/",
            state=self.set_state(state),
            auth_data=auth_data,
            user_agent=user_agent
        )
        self.request_url = reduce(urljoin, [self.base_url, self.path, "repos/search"])
        self.topics_url_template = reduce(urljoin, [self.base_url, self.path, "repos/{}/{}/topics"])

    @classmethod
    def set_state(cls, state: dict = None) -> dict:
        state["per_page"] = state.get("per_page", GITEA_PER_PAGE_MAX)
        state = super().set_state(state)
        return state

    def crawl_repo_topics(self, repo_dict: dict):
        owner_login = repo_dict["owner"]["login"]
        repo_name = repo_dict["name"]
        try:
            topics_url = self.topics_url_template.format(owner_login, repo_name)
            response = self.requests.get(topics_url)
            if not response.ok:
                logger.warning(f"(skipping repo topics) gitea - {topics_url} " +
                               f"- response not ok, status: {response.status_code}")
                return []
            return response.json()[GITEA_REPO_TOPICS_KEY]

        except Exception as e:
            logger.exception(f"(skipping repo topics: {owner_login}/{repo_name}) crawling topics crashed")
            return []

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
                    logger.warning(f"(skipping block chunk) gitea - {self.base_url} " +
                                   f"- response not ok, status: {response.status_code}")
                    return False, [], state  # nr.1 - we skip rest of this block, hope we get it next time
                repo_list = response.json()["data"]
                if not state.get("exclude_topics", False):
                    for repo_dict in repo_list:
                        # TODO unless we request topics in parallel, this slows down crawling by about 20x
                        # TODO if not acceptable over time, subprocess each request
                        repo_dict[GITEA_REPO_TOPICS_KEY] = self.crawl_repo_topics(repo_dict=repo_dict)
            except Exception as e:
                logger.exception(f"(skipping block chunk) gitea crawler crashed")
                return False, [], state  # nr.2 - we skip rest of this block, hope we get it next time

            state['is_done'] = len(repo_list) != state['per_page']  # finish early, we reached the end

            yield True, repo_list, state
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
