from lib.platforms.gitea import GiteaIndexer
from lib.platforms.github import GitHubIndexer
from lib.platforms.gitlab import GitLabIndexer
from lib.platforms.bitbucket import BitBucketIndexer

platforms = {
    GiteaIndexer.name: GiteaIndexer,
    GitHubIndexer.name: GitHubIndexer,
    GitLabIndexer.name: GitLabIndexer,
    BitBucketIndexer.name: BitBucketIndexer
}
