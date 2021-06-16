"""
This crawler goes through GitHub via their GraphQL API.
Either by guessing and incrementing repository IDs, or by asking for known IDs,
we can run queries for a maximum of 100 repositories at a time.
"""
import pathlib
import logging
import time
import base64
from typing import List, Tuple
from urllib.parse import urljoin
from iso8601 import iso8601

from crawlers.lib.platforms.i_crawler import IResult, ICrawler
from crawlers.constants import GITHUB_QUERY_MAX, JOB_FROM_ID, JOB_TO_ID, JOB_IDS

logger = logging.getLogger(__name__)


def get_query():
    current_folder_path = pathlib.Path(__file__).parent.absolute()
    with open(current_folder_path.joinpath("query_repos_batch.graphql")) as f:
        query = f.read()
    return query


query_repos_batch = get_query()


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
        self.repository_id = repository_id
        self.name_with_owner = name_with_owner
        self.homepage_url = homepage_url
        self.updated_at = updated_at
        self.short_description_html = short_description_html
        self.is_archived = is_archived
        self.is_private = is_private
        self.is_fork = is_fork
        self.is_empty = is_empty
        self.is_disabled = is_disabled
        self.is_locked = is_locked
        self.is_template = is_template
        self.stargazer_count = stargazer_count
        self.fork_count = fork_count
        self.disk_usage = disk_usage
        self.repository_topics = repository_topics


class GitHubV4Crawler(ICrawler):
    """ Crawler retrieving data from GitHubs GraphQL API. """

    name = 'github'

    def __init__(self, id, type, base_url, state=None, auth_data=None, user_agent=None, query=query_repos_batch, **kwargs):
        super().__init__(
            _id=id,
            type=type,
            base_url=base_url,
            path='graphql',
            state=state,
            auth_data=auth_data,
            user_agent=user_agent
        )
        self.query = query
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
    def set_state(state: dict = None) -> dict:
        """ Init and update state between each query. """
        if not state:
            state = {}
        state['i'] = state.get('i', -1) + 1  # recursion index
        state[JOB_IDS] = state.get(JOB_IDS, [])  # list when we have known indexes to use as IDs
        state[JOB_FROM_ID] = state.get(JOB_FROM_ID, 0)  # without known IDs, we start from the lowest ID number
        state[JOB_TO_ID] = state.get(JOB_TO_ID, -1)
        state['current'] = state.get('current', 1)  # as in the last/highest ID of the current batch
        state['empty_page_cnt'] = state.get('empty_page_cnt', 0)
        return state

    @staticmethod
    def get_graphql_variables(state: dict) -> dict:
        """ Get a dict with keys representing variables used in a GraphQl query. """
        return {
            "ids": GitHubV4Crawler.get_ids(state)
        }

    @staticmethod
    def get_ids(state: dict) -> list:
        """ Produce a subset of repository IDs from a larger known set, or a exploratory range within query max."""
        # we use known IDs when we have them, otherwise explore incrementally
        i = state['i'] * GITHUB_QUERY_MAX
        if len(state[JOB_IDS]) > 0:
            indexes = state[JOB_IDS][i:i + GITHUB_QUERY_MAX]
        else:
            indexes = range(i, i + GITHUB_QUERY_MAX)

        state['current'] += GITHUB_QUERY_MAX
        return list(map(GitHubV4Crawler.encode_id, indexes))

    @staticmethod
    def encode_id(index: int) -> str:
        """ Base64 encode a complete GitHub repository ID from it's decoded numerical part. """
        return str(base64.b64encode(f"010:Repository{index}".encode()), "utf-8")

    @staticmethod
    def remove_invalid_nodes(nodes: list) -> iter:
        """ Filter out potential null/None values for failed IDs. """
        def exists(result):
            return result is not None
        return filter(exists, nodes)

    @staticmethod
    def has_next_crawl(state: dict) -> bool:
        """ Decide if there are more repositories to crawl for, within current job. """
        return (state[JOB_TO_ID] == -1 or state['current'] < state[JOB_TO_ID]) \
               and state['empty_page_cnt'] < 10

    def crawl(self, state: dict = None) -> Tuple[bool, List[GitHubV4Result], dict]:
        """ Run a GraphQL query against GitHubs V4 API. """
        state = self.set_state(state)
        while self.has_next_crawl(state):
            response = self.requests.post(
                urljoin(self.base_url, self.path),
                json=dict(query=self.query, variables=self.get_graphql_variables(state))
            )
            try:
                nodes = response.json()['data']['nodes']
                valid_nodes = self.remove_invalid_nodes(nodes)
                repos = list(map(self.parse_node, valid_nodes))

                if len(repos) == 0:
                    state['empty_page_cnt'] += 1

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
