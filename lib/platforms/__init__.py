from lib.platforms.gitea import GiteaIndexer
from lib.platforms.github import GitHubIndexer
from lib.platforms.gitlab import GitLabIndexer
from lib.platforms.bitbucket import BitBucketIndexer
from lib.platforms.github_v4 import GitHubIndexerV4

platforms = {
    GiteaIndexer.name: GiteaIndexer,
    GitHubIndexer.name: GitHubIndexer,
    GitLabIndexer.name: GitLabIndexer,
    BitBucketIndexer.name: BitBucketIndexer,
    #GitHubIndexerV4.name: GitHubIndexerV4
}
