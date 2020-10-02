from lib.platforms.gitea import GiteaSearch
from lib.platforms.github import GitHubSearch


platforms = {
    GiteaSearch.name: GiteaSearch,
    GitHubSearch.name: GitHubSearch
}
