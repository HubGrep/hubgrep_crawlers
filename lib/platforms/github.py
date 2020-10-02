import logging
import time
from urllib.parse import urljoin

from iso8601 import iso8601
from lib.platforms._generic import GenericResult, GenericCrawler

logger = logging.getLogger(__name__)


class GitHubResult(GenericResult):
    """
    {'id': 1,
        'node_id': 'MDEwOlJlcG9zaXRvcnkx',
        'name': 'grit',
        'full_name': 'mojombo/grit',
        'private': False,
        'owner': {'login': 'mojombo',
                  'id': 1,
                  'node_id': 'MDQ6VXNlcjE=',
                  'avatar_url': 'https://avatars0.githubusercontent.com/u/1?v=4',
                  'gravatar_id': '',
                  'url': 'https://api.github.com/users/mojombo',
                  'html_url': 'https://github.com/mojombo',
                  'followers_url': 'https://api.github.com/users/mojombo/followers',
                  'following_url': 'https://api.github.com/users/mojombo/following{/other_user}',
                  'gists_url': 'https://api.github.com/users/mojombo/gists{/gist_id}',
                  'starred_url': 'https://api.github.com/users/mojombo/starred{/owner}{/repo}',
                  'subscriptions_url': 'https://api.github.com/users/mojombo/subscriptions',
                  'organizations_url': 'https://api.github.com/users/mojombo/orgs',
                  'repos_url': 'https://api.github.com/users/mojombo/repos',
                  'events_url': 'https://api.github.com/users/mojombo/events{/privacy}',
                  'received_events_url': 'https://api.github.com/users/mojombo/received_events',
                  'type': 'User',
                  'site_admin': False},
        'html_url': 'https://github.com/mojombo/grit',
        'description': '**Grit is no longer maintained. Check out libgit2/rugged.** Grit gives you object oriented read/write access to Git repositories via Ruby.',
        'fork': False,
        'url': 'https://api.github.com/repos/mojombo/grit',
        'forks_url': 'https://api.github.com/repos/mojombo/grit/forks',
        'keys_url': 'https://api.github.com/repos/mojombo/grit/keys{/key_id}',
        'collaborators_url': 'https://api.github.com/repos/mojombo/grit/collaborators{/collaborator}',
        'teams_url': 'https://api.github.com/repos/mojombo/grit/teams',
        'hooks_url': 'https://api.github.com/repos/mojombo/grit/hooks',
        'issue_events_url': 'https://api.github.com/repos/mojombo/grit/issues/events{/number}',
        'events_url': 'https://api.github.com/repos/mojombo/grit/events',
        'assignees_url': 'https://api.github.com/repos/mojombo/grit/assignees{/user}',
        'branches_url': 'https://api.github.com/repos/mojombo/grit/branches{/branch}',
        'tags_url': 'https://api.github.com/repos/mojombo/grit/tags',
        'blobs_url': 'https://api.github.com/repos/mojombo/grit/git/blobs{/sha}',
        'git_tags_url': 'https://api.github.com/repos/mojombo/grit/git/tags{/sha}',
        'git_refs_url': 'https://api.github.com/repos/mojombo/grit/git/refs{/sha}',
        'trees_url': 'https://api.github.com/repos/mojombo/grit/git/trees{/sha}',
        'statuses_url': 'https://api.github.com/repos/mojombo/grit/statuses/{sha}',
        'languages_url': 'https://api.github.com/repos/mojombo/grit/languages',
        'stargazers_url': 'https://api.github.com/repos/mojombo/grit/stargazers',
        'contributors_url': 'https://api.github.com/repos/mojombo/grit/contributors',
        'subscribers_url': 'https://api.github.com/repos/mojombo/grit/subscribers',
        'subscription_url': 'https://api.github.com/repos/mojombo/grit/subscription',
        'commits_url': 'https://api.github.com/repos/mojombo/grit/commits{/sha}',
        'git_commits_url': 'https://api.github.com/repos/mojombo/grit/git/commits{/sha}',
        'comments_url': 'https://api.github.com/repos/mojombo/grit/comments{/number}',
        'issue_comment_url': 'https://api.github.com/repos/mojombo/grit/issues/comments{/number}',
        'contents_url': 'https://api.github.com/repos/mojombo/grit/contents/{+path}',
        'compare_url': 'https://api.github.com/repos/mojombo/grit/compare/{base}...{head}',
        'merges_url': 'https://api.github.com/repos/mojombo/grit/merges',
        'archive_url': 'https://api.github.com/repos/mojombo/grit/{archive_format}{/ref}',
        'downloads_url': 'https://api.github.com/repos/mojombo/grit/downloads',
        'issues_url': 'https://api.github.com/repos/mojombo/grit/issues{/number}',
        'pulls_url': 'https://api.github.com/repos/mojombo/grit/pulls{/number}',
        'milestones_url': 'https://api.github.com/repos/mojombo/grit/milestones{/number}',
        'notifications_url': 'https://api.github.com/repos/mojombo/grit/notifications{?since,all,participating}',
        'labels_url': 'https://api.github.com/repos/mojombo/grit/labels{/name}',
        'releases_url': 'https://api.github.com/repos/mojombo/grit/releases{/id}',
        'deployments_url': 'https://api.github.com/repos/mojombo/grit/deployments'}
    """

    def __init__(self, platform_id, search_result_item):
        name = search_result_item['name']
        owner_name = search_result_item['owner']['login']
        description = search_result_item['description'] or '?'
        last_commit = None
        created_at = None
        language = None
        license = None

        html_url = search_result_item['html_url']

        super().__init__(platform_id=platform_id, name=name,
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

    def __init__(self, platform_id, base_url):
        super().__init__(
            platform_id=platform_id,
            base_url=base_url,
            path='/repositories')
        self.request_url = urljoin(self.base_url, self.path)

    def crawl(self, state=None):
        if not state:
            url = self.request_url
        else:
            url = state.get('url', False)
            if not url:
                logger.warning('{self} broken state, defaulting to start')
                url = self.request_url

        while url:
            try:
                response = self.requests.get(url)
                response.raise_for_status()
            except Exception as e:
                logger.error(e)

                # todo: test this
                logger.warning(
                    f'{self} sleeping for 10min...')
                time.sleep(60 * 10)
                continue

            result = response.json()
            results = [GitHubResult(self.platform_id, item)
                       for item in result]
            state = {'url': url}
            yield True, results, state

            h = response.headers

            ratelimit_remaining = int(h.get('X-Ratelimit-Remaining'))
            # reset at timestamp
            ratelimit_reset = int(h.get('X-Ratelimit-Reset'))
            reset_in = ratelimit_reset - time.time()

            # https://stackoverflow.com/questions/32312758/python-requests-link-headers
            url = response.links.get('next', False)
            url = url.get('url', False)

            logger.info(
                f'{self} {ratelimit_remaining} requests remaining, reset in {reset_in}s')
            if ratelimit_remaining < 1 and url:
                logger.warning(
                    f'{self} rate limiting: {ratelimit_remaining} requests remaining, sleeping {reset_in}s')
                time.sleep(reset_in)
            time.sleep(.5)
