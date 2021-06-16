""" HubGrep constants """

# app
APP_ENV_BUILD = "build"
APP_ENV_DEVELOPMENT = "development"
APP_ENV_PRODUCTION = "production"
APP_ENV_TESTING = "testing"

# threading
THREAD_CRAWLER_NAME = "auto_crawler"

# crawler generic
CRAWLER_IS_RUNNING_ENV_KEY = "crawler_is_running"

# GitHub v4
GITHUB_QUERY_MAX = 100

# keys expected in job data (requested from hubgrep-indexer)
JOB_UID = "uid"
JOB_STATUS = "status"
JOB_ATTEMPTS_AT = "attempts_at"
JOB_FROM_ID = "from_id"
JOB_TO_ID = "to_id"
JOB_IDS = "ids"
JOB_CALLBACK_URL = "callback_url"
