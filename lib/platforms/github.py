import logging
import time
from urllib.parse import urljoin

import requests
from iso8601 import iso8601
from lib.platforms._generic import GenericResult, GenericCrawler

logger = logging.getLogger(__name__)


class GitHubResult(GenericResult):
    """
    {
    "id": 1296269,
    "node_id": "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
    "name": "Hello-World",
    "full_name": "octocat/Hello-World",
    "owner": {
      "login": "octocat",
      "id": 1,
      "node_id": "MDQ6VXNlcjE=",
      "avatar_url": "https://github.com/images/error/octocat_happy.gif",
      "gravatar_id": "",
      "url": "https://api.github.com/users/octocat",
      "html_url": "https://github.com/octocat",
      "followers_url": "https://api.github.com/users/octocat/followers",
      "following_url": "https://api.github.com/users/octocat/following{/other_user}",
      "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
      "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
      "organizations_url": "https://api.github.com/users/octocat/orgs",
      "repos_url": "https://api.github.com/users/octocat/repos",
      "events_url": "https://api.github.com/users/octocat/events{/privacy}",
      "received_events_url": "https://api.github.com/users/octocat/received_events",
      "type": "User",
      "site_admin": false
    },
    "private": false,
    "html_url": "https://github.com/octocat/Hello-World",
    "description": "This your first repo!",
    "fork": false,
    "url": "https://api.github.com/repos/octocat/Hello-World",
    "archive_url": "https://api.github.com/repos/octocat/Hello-World/{archive_format}{/ref}",
    "assignees_url": "https://api.github.com/repos/octocat/Hello-World/assignees{/user}",
    "blobs_url": "https://api.github.com/repos/octocat/Hello-World/git/blobs{/sha}",
    "branches_url": "https://api.github.com/repos/octocat/Hello-World/branches{/branch}",
    "collaborators_url": "https://api.github.com/repos/octocat/Hello-World/collaborators{/collaborator}",
    "comments_url": "https://api.github.com/repos/octocat/Hello-World/comments{/number}",
    "commits_url": "https://api.github.com/repos/octocat/Hello-World/commits{/sha}",
    "compare_url": "https://api.github.com/repos/octocat/Hello-World/compare/{base}...{head}",
    "contents_url": "https://api.github.com/repos/octocat/Hello-World/contents/{+path}",
    "contributors_url": "https://api.github.com/repos/octocat/Hello-World/contributors",
    "deployments_url": "https://api.github.com/repos/octocat/Hello-World/deployments",
    "downloads_url": "https://api.github.com/repos/octocat/Hello-World/downloads",
    "events_url": "https://api.github.com/repos/octocat/Hello-World/events",
    "forks_url": "https://api.github.com/repos/octocat/Hello-World/forks",
    "git_commits_url": "https://api.github.com/repos/octocat/Hello-World/git/commits{/sha}",
    "git_refs_url": "https://api.github.com/repos/octocat/Hello-World/git/refs{/sha}",
    "git_tags_url": "https://api.github.com/repos/octocat/Hello-World/git/tags{/sha}",
    "git_url": "git:github.com/octocat/Hello-World.git",
    "issue_comment_url": "https://api.github.com/repos/octocat/Hello-World/issues/comments{/number}",
    "issue_events_url": "https://api.github.com/repos/octocat/Hello-World/issues/events{/number}",
    "issues_url": "https://api.github.com/repos/octocat/Hello-World/issues{/number}",
    "keys_url": "https://api.github.com/repos/octocat/Hello-World/keys{/key_id}",
    "labels_url": "https://api.github.com/repos/octocat/Hello-World/labels{/name}",
    "languages_url": "https://api.github.com/repos/octocat/Hello-World/languages",
    "merges_url": "https://api.github.com/repos/octocat/Hello-World/merges",
    "milestones_url": "https://api.github.com/repos/octocat/Hello-World/milestones{/number}",
    "notifications_url": "https://api.github.com/repos/octocat/Hello-World/notifications{?since,all,participating}",
    "pulls_url": "https://api.github.com/repos/octocat/Hello-World/pulls{/number}",
    "releases_url": "https://api.github.com/repos/octocat/Hello-World/releases{/id}",
    "ssh_url": "git@github.com:octocat/Hello-World.git",
    "stargazers_url": "https://api.github.com/repos/octocat/Hello-World/stargazers",
    "statuses_url": "https://api.github.com/repos/octocat/Hello-World/statuses/{sha}",
    "subscribers_url": "https://api.github.com/repos/octocat/Hello-World/subscribers",
    "subscription_url": "https://api.github.com/repos/octocat/Hello-World/subscription",
    "tags_url": "https://api.github.com/repos/octocat/Hello-World/tags",
    "teams_url": "https://api.github.com/repos/octocat/Hello-World/teams",
    "trees_url": "https://api.github.com/repos/octocat/Hello-World/git/trees{/sha}",
    "clone_url": "https://github.com/octocat/Hello-World.git",
    "mirror_url": "git:git.example.com/octocat/Hello-World",
    "hooks_url": "https://api.github.com/repos/octocat/Hello-World/hooks",
    "svn_url": "https://svn.github.com/octocat/Hello-World",
    "homepage": "https://github.com",
    "language": null,
    "forks_count": 9,
    "stargazers_count": 80,
    "watchers_count": 80,
    "size": 108,
    "default_branch": "master",
    "open_issues_count": 0,
    "is_template": true,
    "topics": [
      "octocat",
      "atom",
      "electron",
      "api"
    ],
    "has_issues": true,
    "has_projects": true,
    "has_wiki": true,
    "has_pages": false,
    "has_downloads": true,
    "archived": false,
    "disabled": false,
    "visibility": "public",
    "pushed_at": "2011-01-26T19:06:43Z",
    "created_at": "2011-01-26T19:01:12Z",
    "updated_at": "2011-01-26T19:14:43Z",
    "permissions": {
      "admin": false,
      "push": false,
      "pull": true
    },
    "template_repository": "octocat/template",
    "temp_clone_token": "ABTLWHOULUVAXGTRYU7OC2876QJ2O",
    "delete_branch_on_merge": true,
    "subscribers_count": 42,
    "network_count": 0,
    "license": {
      "key": "mit",
      "name": "MIT License",
      "spdx_id": "MIT",
      "url": "https://api.github.com/licenses/mit",
      "node_id": "MDc6TGljZW5zZW1pdA=="
    }
  }
    """
    def __init__(self, platform_id, search_result_item):
        name = search_result_item['name']
        owner = search_result_item.get('owner', {})
        if owner:
            owner_name = owner.get('login', None)
        else:
            owner_name = None
        description = search_result_item['description'] or ''
        last_commit = None
        created_at = iso8601.parse_date(search_result_item['created_at'])
        language = None
        license = None

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


class GitHubSearch(GenericCrawler):
    """
    Accept-Ranges: bytes
    Content-Length: 32867
    X-GitHub-Request-Id: DE4C:7325:72FE05F:88CCA3F:5F74ECF6
    X-Ratelimit-Limit: 60
    X-Ratelimit-Remaining: 46
    X-Ratelimit-Reset: 1601501700
    X-Ratelimit-Used: 14
    access-control-allow-origin: *
    access-control-expose-headers: ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Used, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, Deprecation, Sunset
    cache-control: public, max-age=60, s-maxage=60
    content-encoding: gzip
    content-security-policy: default-src 'none'
    content-type: application/json; charset=utf-8
    date: Wed, 30 Sep 2020 20:39:07 GMT
    etag: W/"f95a90519ac2d5dbc76753515500268383c3b666f6fdaf187d82444e25ba14a5"
    link: <https://api.github.com/repositories?since=369>; rel="next", <https://api.github.com/repositories{?since}>; rel="first"
    referrer-policy: origin-when-cross-origin, strict-origin-when-cross-origin
    server: GitHub.com
    status: 200 OK
    strict-transport-security: max-age=31536000; includeSubdomains; preload
    vary: Accept, Accept-Encoding, Accept, X-Requested-With, Accept-Encoding
    x-content-type-options: nosniff
    x-frame-options: deny
    x-github-media-type: github.v3; format=json
    x-xss-protection: 1; mode=block
    """

    name = 'github'

    def __init__(self, id, base_url, state=None, auth_data=None, **kwargs):
        super().__init__(
            _id=id,
            base_url=base_url,
            path='',
            state=state,
            auth_data=auth_data
        )
        self.request_url = urljoin(self.base_url, self.path)
        if auth_data:
            self.requests.auth = (
                auth_data['client_id'],
                auth_data['client_secret'])

    def request(self, url, params=None):
        response = False
        while not response:
            try:
                response = self.requests.get(url, params=params)
                response.raise_for_status()
            except Exception as e:
                logger.error(e)

                # todo: test this
                logger.warning(
                    f'{self} sleeping for 10min...')
                time.sleep(60 * 10)
                response = False
        return response

    def handle_ratelimit(self, response):
        h = response.headers
        ratelimit_remaining = int(h.get('X-Ratelimit-Remaining'))
        ratelimit_reset_timestamp = int(h.get('X-Ratelimit-Reset'))
        reset_in = ratelimit_reset_timestamp - time.time()

        logger.info(
            f'{self} {ratelimit_remaining} requests remaining, reset in {reset_in}s')
        if ratelimit_remaining < 1:
            logger.warning(
                f'{self} rate limiting: {ratelimit_remaining} requests remaining, sleeping {reset_in}s')
            time.sleep(reset_in)

    def get_user_repos(self, user_repos_url):
        while user_repos_url:
            response = self.request(user_repos_url, params=dict(per_page=100))
            results = [GitHubResult(self._id, item)
                       for item in response.json()]

            yield results

            self.handle_ratelimit(response)
            header_next = response.links.get('next', {})
            user_repos_url = header_next.get('url', False)

    def crawl(self, state=None):
        user_url = False
        if state:
            user_url = state.get('user_url', False)
            if not user_url:
                logger.warning('{self} broken state, defaulting to start')

        if not user_url:
            user_url = '/users'

        while user_url:
            user_response = self.request(urljoin(self.base_url, user_url))
            self.handle_ratelimit(user_response)

            users_page = user_response.json()
            for user in users_page:
                user_repos = []
                for repo_page in self.get_user_repos(user['repos_url']):
                    logger.debug(f'{self} {len(repo_page)} repos in page')
                    user_repos += repo_page
                state = {'user_url': user_url}
                yield True, user_repos, state

            # https://stackoverflow.com/questions/32312758/python-requests-link-headers
            user_header_next = user_response.links.get('next', {})
            user_url = user_header_next.get('url', False)
            if not user_url:
                # not hit rate limit, and we dont have a next url - finished!
                # reset state
                yield True, [], None
            time.sleep(.01)
