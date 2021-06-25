"""
HubGrep crawlers Flask-app initialization script
"""
import logging
import os
from werkzeug.serving import WSGIRequestHandler
from flask import Flask

from crawlers.constants import APP_ENV_BUILD, APP_ENV_DEVELOPMENT, APP_ENV_PRODUCTION, APP_ENV_TESTING
from crawlers.lib.init_logging import init_logging
from crawlers.api_blueprint import api_bp
from crawlers.cli_blueprint import cli_bp

logger = logging.getLogger(__name__)

# fix keep-alive in dev server (dropped connections from client sessions)
WSGIRequestHandler.protocol_version = "HTTP/1.1"


def create_app():
    """ Create a Flask-app for HubGrep crawlers. """
    app = Flask(__name__)

    config_mapping = {
        APP_ENV_BUILD: "crawlers.config.BuildConfig",
        APP_ENV_DEVELOPMENT: "crawlers.config.DevelopmentConfig",
        APP_ENV_PRODUCTION: "crawlers.config.ProductionConfig",
        APP_ENV_TESTING: "crawlers.config.TestingConfig",
    }

    app_env = os.environ.get("APP_ENV", APP_ENV_DEVELOPMENT)
    app.config.from_object(config_mapping[app_env])

    init_logging(loglevel=app.config["LOGLEVEL"])

    app.register_blueprint(api_bp)
    app.register_blueprint(cli_bp)

    return app
