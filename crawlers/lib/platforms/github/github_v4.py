"""
This crawler goes through GitHub via their GraphQL API.
By guessing and incrementing repository IDs, we do direct
queries for 100 repositories at a time.
"""
import pathlib
import logging
import time
import base64
from typing import List
from urllib.parse import urljoin
from iso8601 import iso8601

from crawlers.lib.platforms.i_crawler import IResult, ICrawler
from crawlers.constants import GITHUB_QUERY_MAX

logger = logging.getLogger(__name__)


def get_query():
    current_folder_path = pathlib.Path(__file__).parent.absolute()
    with open(current_folder_path.joinpath("query_repos_batch.graphql")) as f:
        query = f.read()
    return query


query = get_query()
per_query = 100  # max-limit that GitHub API imposes


class GitHubV4Result(IResult):
    """
    GitHub V4 - graphql results.

    Parameters except for platform_id should be in the same order as they are listed in the query.
    """

    def __init__(self, platform_id,
                 repository_id: str,
                 repository_name: str,
                 name_with_owner: str,
                 homepage_url: str,
                 url: str,
                 created_at: str,
                 updated_at: str,
                 pushed_at: str,
                 short_description_html: str,
                 description: str,
                 is_archived: bool,
                 is_private: bool,
                 is_fork: bool,
                 is_empty: bool,
                 is_disabled: bool,
                 is_locked: bool,
                 is_template: bool,
                 stargazer_count: int,
                 fork_count: int,
                 disk_usage: int,
                 owner_name: str,
                 repository_topics: list,
                 language_name: str,
                 license_name: str):
        if pushed_at:
            last_commit = iso8601.parse_date(pushed_at)
        else:
            last_commit = None
        # TODO store everything!
        super().__init__(platform_id=platform_id,
                         name=repository_name,
                         description=description,
                         html_url=url,
                         owner_name=owner_name,
                         last_commit=last_commit,
                         created_at=created_at,
                         language=language_name,
                         license=license_name)


class GitHubV4Crawler(ICrawler):
    """ Crawl the GitHub graphql api """

    name = 'github'

    def __init__(self, id, base_url, state=None, auth_data=None, **kwargs):
        super().__init__(
            _id=id,
            base_url=base_url,
            path='graphql',
            state=state,
            auth_data=auth_data
        )
        self.request_url = urljoin(self.base_url, self.path)
        if auth_data:
            self.requests.headers.update(
                {"Authorization": f"Bearer {auth_data['access_token']}"})

    def handle_ratelimit(self, response):
        """
        Adjust requests to API limits

        {
          "data": {
            "rateLimit": {
              "cost": 1,
              "remaining": 4984,
              "resetAt": "2020-11-29T14:26:15Z"
            },
        """
        rate_limit = response.json().get('data').get('rateLimit')
        ratelimit_remaining = rate_limit['remaining']

        reset_at = iso8601.parse_date(rate_limit['resetAt'])
        ratelimit_reset_timestamp = reset_at.timestamp()

        reset_in = ratelimit_reset_timestamp - time.time()

        logger.info(
            f'{self} {ratelimit_remaining} requests remaining, reset in {reset_in}s')
        if ratelimit_remaining < 1:
            logger.warning(
                f'{self} rate limiting: {ratelimit_remaining} requests remaining, sleeping {reset_in}s')
            time.sleep(reset_in)

    @staticmethod
    def init_state(state=None) -> dict:
        if not state:
            state = {}
        state['start_at'] = state.get('start_at', 1)  # github starts at repo nr.1
        state['end_at'] = state.get('end_at', -1)
        state['current'] = state.get('current', 1)
        state['empty_page_cnt'] = state.get('empty_page_cnt', 0)
        return state

    @staticmethod
    def get_variables(state) -> dict:
        return {
            "ids": GitHubV4Crawler.get_ids(state)
        }

    @staticmethod
    def get_ids(state) -> list:
        nr_range = range(state['current'], state['current'] + GITHUB_QUERY_MAX)
        return list(map(GitHubV4Crawler.encode_id, nr_range))

    @staticmethod
    def encode_id(index: int) -> str:
        return str(base64.b64encode(f"010:Repository{index}".encode()), "utf-8")

    @staticmethod
    def remove_invalid_nodes(nodes: list) -> iter:
        """ Filter out potential null/None values for failed IDs. """
        def exists(result):
            return result is not None
        return filter(exists, nodes)

    @staticmethod
    def has_next_crawl(state) -> bool:
        return (state['end_at'] == -1 or state['current'] < state['end_at']) \
               and state['empty_page_cnt'] < 10

    def crawl(self, state=None):
        state = self.init_state(state)
        while self.has_next_crawl(state):
            response = self.requests.post(
                urljoin(self.base_url, self.path),
                json=dict(query=query, variables=self.get_variables(state))
            )
            try:
                nodes = response.json()['data']['nodes']
                valid_nodes = self.remove_invalid_nodes(nodes)
                repos = list(map(self.parse_node, valid_nodes))

                if len(repos) == 0:
                    state['empty_page_cnt'] += 1

                state['current'] += GITHUB_QUERY_MAX

                yield True, repos, state
                self.handle_ratelimit(response)

            except Exception as e:
                logger.error(f'node parsing failed. response was: {response.json()}')
                raise e
            time.sleep(.01)  # self-throttle to play nice

    def parse_node(self, node: dict) -> GitHubV4Result:
        """
        Default parser for responses without errors.

        {
          "data": {
            "nodes": [
              {
                "id": "MDEwOlJlcG9zaXRvcnkxNzU1ODIyNg==",
                "name": "service.subtitles.thelastfantasy",
                "nameWithOwner": "taxigps/service.subtitles.thelastfantasy",
                "homepageUrl": null,
                "url": "https://github.com/taxigps/service.subtitles.thelastfantasy",
                "createdAt": "2014-03-09T05:10:10Z",
                "updatedAt": "2014-03-09T16:57:19Z",
                "pushedAt": "2014-03-09T16:57:19Z",
                "shortDescriptionHTML": "",
                "description": null,
                "isArchived": false,
                "isPrivate": false,
                "isFork": false,
                "isEmpty": false,
                "isDisabled": false,
                "isLocked": false,
                "isTemplate": false,
                "stargazerCount": 0,
                "forkCount": 0,
                "diskUsage": 192,
                "owner": {
                    "login": "taxigps",
                    "id": "MDQ6VXNlcjEwMjQzNA==",
                    "url": "https://github.com/taxigps"
                },
                "repositoryTopics": {
                    "nodes": []
                },
                "primaryLanguage": {
                    "name": "Python"
                },
                "licenseInfo": {
                    "name": "GNU General Public License v2.0",
                    "nickname": "GNU GPLv2"
                }
              }
            ]
          }
        }
        """
        try:
            created_at = node["createdAt"] or ""
            updated_at = node["updatedAt"] or ""
            pushed_at = node["pushedAt"] or ""
            owner_name = node["owner"] or {}
            owner_name = owner_name.get("login", None)
            language = node["primaryLanguage"] or {}
            language = language.get("name", None)
            license_name = node["licenseInfo"] or {}
            license_name = license_name.get("name", None)
            repository_topics = node["repositoryTopics"] or {"nodes": []}
            repository_topics = [topic.get("name", None) for topic in repository_topics["nodes"]]
            return GitHubV4Result(platform_id=self._id,
                                  repository_id=node["id"],
                                  repository_name=node["name"],
                                  name_with_owner=node["nameWithOwner"],
                                  homepage_url=node["homepageUrl"],
                                  url=node["url"],
                                  created_at=created_at,
                                  updated_at=updated_at,
                                  pushed_at=pushed_at,
                                  short_description_html=node["shortDescriptionHTML"],
                                  description=node["description"],
                                  is_archived=node["isArchived"],
                                  is_private=node["isPrivate"],
                                  is_fork=node["isFork"],
                                  is_empty=node["isEmpty"],
                                  is_disabled=node["isDisabled"],
                                  is_locked=node["isLocked"],
                                  is_template=node["isTemplate"],
                                  stargazer_count=node["stargazerCount"],
                                  fork_count=node["forkCount"],
                                  disk_usage=node["diskUsage"],
                                  owner_name=owner_name,
                                  repository_topics=repository_topics,
                                  language_name=language,
                                  license_name=license_name)
        except KeyError as e:
            logger.error(f'node -DICT- parsing failed.\n- repo node was: {node}\n- error key: {e}')
            # TODO return something we can filter out, so that we still collect other results
