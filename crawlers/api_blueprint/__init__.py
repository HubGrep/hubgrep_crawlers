from flask import Blueprint

api_bp = Blueprint("api", __name__)

from crawlers.api_blueprint.routes import crawl
