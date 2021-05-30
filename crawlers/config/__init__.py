"""
HubGrep environment configurations.
"""


class Config:
    """ Base configuration. """
    # hardcoded config
    DEBUG = False
    TESTING = False
    LOGLEVEL = "debug"
    VERSION = "0.0.0"


class ProductionConfig(Config):
    """ Production Configuration. """
    DEBUG = False


class DevelopmentConfig(Config):
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
