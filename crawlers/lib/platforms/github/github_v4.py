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
from requests import Response

from crawlers.lib.platforms.i_crawler import ICrawler
from crawlers.constants import (
    GITHUB_QUERY_MAX, BLOCK_KEY_FROM_ID, BLOCK_KEY_TO_ID, BLOCK_KEY_IDS, GITHUB_API_ABUSE_SLEEP
)

logger = logging.getLogger(__name__)


def get_query():
    current_folder_path = pathlib.Path(__file__).parent.absolute()
    with open(current_folder_path.joinpath("query_repos_batch.graphql")) as f:
        query = f.read()
    return query


query_repos_batch = get_query()


class GitHubV4Crawler(ICrawler):
    """ Crawler retrieving data from GitHubs GraphQL API. """

    name = 'github'

    def __init__(self, base_url, state=None, auth_data=None, user_agent=None, query=query_repos_batch, **kwargs):
        super().__init__(
            base_url=base_url,
            path='graphql',
            state=self.set_state(state),
            auth_data=auth_data,
            user_agent=user_agent
        )
        self.query = query
        self.request_url = urljoin(self.base_url, self.path)
        if auth_data:
            self.requests.headers.update(
                {"Authorization": f"Bearer {auth_data['access_token']}"})

    def handle_ratelimit(self, response=None):
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
        if response is not None:
            rate_limit = response.json().get("data", {}).get('rateLimit', None)
            if rate_limit:
                ratelimit_remaining = rate_limit['remaining']
                reset_at = iso8601.parse_date(rate_limit['resetAt'])
                ratelimit_reset_timestamp = reset_at.timestamp()

                reset_in = ratelimit_reset_timestamp - time.time()
                # a bit longer, just to be sure
                reset_in += 1

                logger.info(
                    f'{self} {ratelimit_remaining} requests remaining, reset in {reset_in}s')
                if ratelimit_remaining < 1:
                    logger.warning(
                        f'{self} rate limiting: {ratelimit_remaining} requests remaining, sleeping {reset_in}s')
                    time.sleep(reset_in)
            else:
                logger.warning("no ratelimit found in github response data")
                super().handle_ratelimit()
        else:
            super().handle_ratelimit()

    @classmethod
    def set_state(cls, state: dict = None) -> dict:
        """
        Init and update state between each query.

        Internally, we prioritize known ids as indicated by JOB_IDS, if they exist.
        Otherwise, we fall back to use JOB_FROM_ID and go until JOB_TO_ID.
        """
        if not state:
            state = {}
        state['i'] = state.get('i', -1) + 1  # increment how many times we have set the state
        state['empty_page_cnt'] = state.get('empty_page_cnt', 0)  # indicate that exploration has reached an end
        if not isinstance(state.get(BLOCK_KEY_IDS, None), list):
            state[BLOCK_KEY_IDS] = []  # list when we have known indexes to use as IDs
        state[BLOCK_KEY_FROM_ID] = state.get(BLOCK_KEY_FROM_ID,
                                             0)  # without known IDs, we start from the lowest ID number
        state[BLOCK_KEY_TO_ID] = state.get(BLOCK_KEY_TO_ID, -1)
        if len(state[BLOCK_KEY_IDS]) > 0:
            state['current'] = state.get('current', state[BLOCK_KEY_IDS][0])
        else:
            state['current'] = state.get('current', state[BLOCK_KEY_FROM_ID])
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
        i = state['i'] * GITHUB_QUERY_MAX
        if len(state[BLOCK_KEY_IDS]) > 0:
            # we use known IDs when we have them
            indexes = state[BLOCK_KEY_IDS][i:i + GITHUB_QUERY_MAX]
            if len(indexes) > 0:
                state['current'] = indexes[-1]
        else:
            # otherwise explore incrementally within from/to
            i += state[BLOCK_KEY_FROM_ID]
            indexes = range(i, i + GITHUB_QUERY_MAX)
            state['current'] += GITHUB_QUERY_MAX

        return list(map(GitHubV4Crawler.encode_id, indexes))

    @staticmethod
    def encode_id(index: int) -> str:
        """ Base64 encode a complete GitHub repository ID from it's decoded numerical part. """
        return str(base64.b64encode(f"010:Repository{index}".encode()), "utf-8")

    @staticmethod
    def remove_invalid_nodes(nodes: list) -> list:
        """ Filter out potential null/None values for failed IDs. """

        def exists(result):
            return result is not None

        return list(filter(exists, nodes))

    @classmethod
    def has_next_crawl(cls, state: dict) -> bool:
        """ Decide if there are more repositories to crawl for, within current job. """
        return (state[BLOCK_KEY_TO_ID] == -1 or state['current'] < state[BLOCK_KEY_TO_ID]) \
               and state['empty_page_cnt'] < 10

    def crawl(self, state: dict = None) -> Tuple[bool, List[dict], dict]:
        """
        Run a GraphQL query against GitHubs V4 API.

        :return: success, repos, state
        """
        state = state or self.state

        def send_query() -> Response:
            variables = self.get_graphql_variables(state)
            return self.requests.post(
                url=self.request_url,
                json=dict(query=self.query, variables=variables)
            )

        while self.has_next_crawl(state):
            try:
                response = send_query()
                while response.status_code == 403:
                    # we sometimes run in to some "hidden" abuse detection on multiple crawlers
                    # it tells use to wait a few minutes, but a few seconds is enough to be allowed again
                    # thus, we repeatedly try again to avoid having holes in our data (skipped block chunks)
                    # TODO don't see a way to avoid triggering this right now
                    # TODO it triggers even though we have plenty of ratelimit to spare
                    logger.warning(
                        f"status 403 sleeping for {GITHUB_API_ABUSE_SLEEP} - probably triggered abuse flag? json:\n{response.json()}")
                    time.sleep(GITHUB_API_ABUSE_SLEEP)
                    response = send_query()

                if response.ok:
                    repos = response.json()['data']['nodes']
                    repos = self.remove_invalid_nodes(repos)
                    if len(repos) == 0:
                        state['empty_page_cnt'] += 1
                    yield True, repos, state
                else:
                    logger.warning(f"(skipping block chunk) github response not ok, status: {response.status_code}")
                    logger.warning(f"headers: {response.headers.__dict__}")
                    logger.warning(f"json: {response.json()}")
                    yield False, [], state
                self.handle_ratelimit(response)

            except Exception as e:
                logger.exception(f"(skipping block chunk) github crawler crashed")
                yield False, [], state
                self.handle_ratelimit()

            state = self.set_state(state)  # update state for next round

        """ expected GraphQL response
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
