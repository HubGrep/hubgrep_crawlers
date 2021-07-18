from typing import Dict, Any, Type, Union
from crawlers.lib.platforms.i_crawler import ICrawler
from crawlers.lib.platforms.gitea import GiteaCrawler
from crawlers.lib.platforms.gitlab import GitLabCrawler
from crawlers.lib.platforms.bitbucket import BitBucketCrawler
from crawlers.lib.platforms.github import GitHubV4Crawler, GitHubRESTCrawler

platforms: Dict[str, ICrawler] = {
    GiteaCrawler.type: GiteaCrawler,
    GitLabCrawler.type: GitLabCrawler,
    GitHubV4Crawler.type: GitHubV4Crawler,
    GitHubRESTCrawler.type: GitHubRESTCrawler,
    BitBucketCrawler.type: BitBucketCrawler,
}

