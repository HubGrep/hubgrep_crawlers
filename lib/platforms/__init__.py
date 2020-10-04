from lib.platforms.gitea import GiteaIndexer
from lib.platforms.github import GitHubIndexer
from lib.platforms.gitlab import GitLabIndexer

platforms = {
    GiteaIndexer.name: GiteaIndexer,
    GitHubIndexer.name: GitHubIndexer,
    GitLabIndexer.name: GitLabIndexer
}
