import logging

from crawlers.lib.db import DB

db = DB()

logger = logging.getLogger(__name__)


def crawl(platforms):
    logger.info(f'crawling {", ".join(str(p) for p in platforms)}')

    for platform in platforms:
        logger.info(f'starting {platform}')
        for success, result_chunk, state in platform.crawl(state=platform.state):
            if success:
                logger.info(f'got {len(result_chunk)} results from {platform}')
                db.repo_add_or_update(result_chunk)
                db.platform_update_state(platform._id, state)
        db.platform_update_state(platform._id, None)
    logger.info(f'finished {", ".join(str(p) for p in platforms)}')
