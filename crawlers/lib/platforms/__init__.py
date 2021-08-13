from typing import Dict
from crawlers.lib.platforms.i_crawler import ICrawler
from crawlers.lib.platforms.gitea import GiteaCrawler
from crawlers.lib.platforms.gitlab import GitLabCrawler
from crawlers.lib.platforms.bitbucket import BitBucketCrawler
from crawlers.lib.platforms.github import GitHubV4Crawler

platforms: Dict[str, ICrawler] = {
    GiteaCrawler.type: GiteaCrawler,
    GitLabCrawler.type: GitLabCrawler,
    GitHubV4Crawler.type: GitHubV4Crawler,
    BitBucketCrawler.type: BitBucketCrawler,
}

