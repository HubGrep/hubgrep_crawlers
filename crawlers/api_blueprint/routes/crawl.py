import logging

from crawlers.api_blueprint import api_bp
from crawlers.lib.db import DB
from crawlers.lib.crawl import crawl

logger = logging.getLogger(__name__)

db = DB()


@api_bp.route("/crawl")
def crawl():
    all_platforms = db.platform_get_all()
    crawl(all_platforms)
