from typing import Dict, Any, Type, Union
from crawlers.lib.platforms.i_crawler import ICrawler
from crawlers.lib.platforms.gitea import GiteaCrawler
from crawlers.lib.platforms.gitlab import GitLabCrawler
from crawlers.lib.platforms.bitbucket import BitBucketCrawler
from crawlers.lib.platforms.github import GitHubV4Crawler, GitHubRESTCrawler

platforms: Dict[Any, Type[Union[GiteaCrawler, GitLabCrawler, GitHubV4Crawler, GitHubRESTCrawler, BitBucketCrawler]]] = {
    GiteaCrawler.name: GiteaCrawler,
    GitLabCrawler.name: GitLabCrawler,
    GitHubV4Crawler.name: GitHubV4Crawler,
    GitHubRESTCrawler.name: GitHubRESTCrawler,
    BitBucketCrawler.name: BitBucketCrawler
}

