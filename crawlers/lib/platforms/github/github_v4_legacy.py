"""
Legacy note:

There is a limit at 1000 results for the search api (both rest and graphql)
https://stackoverflow.com/questions/48371313/github-api-pagination-limit
https://developer.github.com/v3/search/#about-the-search-api

This version is not usable for us as we cannot get around this limit!
"""
import pathlib
import logging
import time
from typing import List, Tuple
from iso8601 import iso8601
from urllib.parse import urljoin

from crawlers.lib.platforms.i_crawler import ICrawler

logger = logging.getLogger(__name__)


def get_query():
    current_folder_path = pathlib.Path(__file__).parent.absolute()
    with open(current_folder_path.joinpath('query_repos_search.graphql')) as f:
        query = f.read()
    return query


query = get_query()


class GitHubResult:
    def __init__(self, search_result_item):
        name = search_result_item['name']
        owner = search_result_item.get('owner', {})
        if owner:
            owner_name = owner.get('login', None)
        else:
            owner_name = None
        description = search_result_item['description'] or ''

        pushed_at = search_result_item.get('pushedAt', False)
        if pushed_at:
            last_commit = iso8601.parse_date(pushed_at)
        else:
            last_commit = None
        created_at = iso8601.parse_date(search_result_item['updatedAt'])
        language = None
        license = None

        html_url = search_result_item['url']

        super().__init__(name=name,
                         description=description,
                         html_url=html_url,
                         owner_name=owner_name,
                         last_commit=last_commit,
                         created_at=created_at,
                         language=language,
                         license=license)


class GitHubV4Crawler(ICrawler):
    """
    """
    name = 'github_v4_legacy'

    def __init__(self, base_url, state=None, auth_data=None, user_agent=None, **kwargs):
        super().__init__(
            base_url=base_url,
            path='graphql',
            state=state,
            auth_data=auth_data,
            user_agent=user_agent
        )
        self.request_url = urljoin(self.base_url, self.path)
        if auth_data:
            self.requests.headers.update(
                {"Authorization": f"Bearer {auth_data['access_token']}"})

    def handle_ratelimit(self, response):
        """
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

    def get_variables(self, cursor):
        # todo: there is no way to order by created_at?
        # -> https://github.community/t/graphql-sorting-search-results/14088/2
        variables = {
            #"queryString": "is:public archived:false created:2020-11-28T13:00:00Z..2020-11-28T14:00:00Z"

            "queryString": "is:public",
            "cursor": cursor,
        }
        return variables

    def crawl(self, state: dict = None) -> Tuple[bool, List[GitHubResult], dict]:
        # crawl all repos, set timestamp for this run
        # delete all repos with older timestamp (these are deleted)
        # start from beginning :)
        cursor = None
        if state:
            cursor = state.get('cursor', None)

        hasNextPage = True
        while hasNextPage:
            variables = self.get_variables(cursor)
            response = self.requests.post(
                urljoin(self.base_url, self.path),
                json=dict(query=query, variables=variables)
            )
            try:
                edges = response.json()['data']['search']['edges']

                page_info = response.json()['data']['search']['pageInfo']
                cursor = page_info['endCursor']
                hasNextPage = page_info['hasNextPage']

                repos = [GitHubResult(result['node'])
                         for result in edges]

                print(len(repos))
                print(hasNextPage)

                state = dict(cursor=cursor)
                yield True, repos, state

                self.handle_ratelimit(response)
            except Exception as e:
                logger.error(f'failed. response was: {response.json()}')
                raise e
            time.sleep(.01)
