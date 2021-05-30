from crawlers.lib.platforms.gitea import GiteaCrawler
from crawlers.lib.platforms.gitlab import GitLabCrawler
from crawlers.lib.platforms.bitbucket import BitBucketCrawler
from crawlers.lib.platforms.github import GitHubV4Crawler, GitHubRESTCrawler

platforms = {
    GiteaCrawler.name: GiteaCrawler,
    GitLabCrawler.name: GitLabCrawler,
    GitHubV4Crawler.name: GitHubV4Crawler,
    GitHubRESTCrawler.name: GitHubRESTCrawler,
    BitBucketCrawler.name: BitBucketCrawler
}
