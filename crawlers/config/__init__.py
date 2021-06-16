"""
HubGrep environment configurations.
"""
import os


class Config:
    """ Base configuration. """
    DEBUG = False
    TESTING = False
    LOGLEVEL = "debug"
    VERSION = "0.0.1"

    CRAWLER_SLEEP_NO_JOB = 5
    IS_AUTO_CRAWL = False


class _EnvironmentConfig(Config):
    CRAWLER_USER_AGENT = f'HobGrebbit v{Config.VERSION} {os.environ.get("HUBGREP_CRAWLERS_USER_AGENT_SUFFIX")}'
    JOB_URL = os.environ.get("HUBGREP_CRAWLERS_JOB_URL", None)

    if JOB_URL is not None:
        IS_AUTO_CRAWL = True


class ProductionConfig(_EnvironmentConfig):
    """ Production Configuration. """
    DEBUG = False


class DevelopmentConfig(_EnvironmentConfig):
    """ Development configuration. """
    DEBUG = True


class BuildConfig(Config):
    """ Build configuration, in bundling and preparation for deployment. """
    TESTING = True
    DEBUG = True


class TestingConfig(Config):
    """ Test configuration, as used by tests. """
    TESTING = True
    DEBUG = True
