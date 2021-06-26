""" HubGrep constants """

# app
APP_ENV_BUILD = "build"
APP_ENV_DEVELOPMENT = "development"
APP_ENV_PRODUCTION = "production"
APP_ENV_TESTING = "testing"

# crawler generic
CRAWLER_IS_RUNNING_ENV_KEY = "crawler_is_running"
CRAWLER_DEFAULT_THROTTLE = 0.1  # (seconds) unless an API has other means of throttling, we self-throttle for this

# GitHub v4
GITHUB_QUERY_MAX = 100

# Gitea
GITEA_PER_PAGE_MAX = 50

# GitLab
GITLAB_PER_PAGE_MAX = 100

# keys expected in block data (requested from hubgrep-indexer)
BLOCK_KEY_UID = "uid"
BLOCK_KEY_STATUS = "status"
BLOCK_KEY_ATTEMPTS_AT = "attempts_at"
BLOCK_KEY_FROM_ID = "from_id"
BLOCK_KEY_TO_ID = "to_id"
BLOCK_KEY_IDS = "ids"
BLOCK_KEY_CALLBACK_URL = "callback_url"
