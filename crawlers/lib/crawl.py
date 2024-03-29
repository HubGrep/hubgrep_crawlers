"""
Main crawler processing.
"""
import logging
import time
import uuid
from typing import List, Generator
from flask import current_app

from crawlers.constants import BLOCK_KEY_CALLBACK_URL

from crawlers.lib.platforms.i_crawler import ICrawler
from crawlers.lib.platforms import platforms

logger = logging.getLogger(__name__)

default_error_sleep = 10
max_errors = 5


def _hoster_session_request(method, session, url, error_count=0, *args, **kwargs):
    try:
        session.headers.update({"X-Request-ID": uuid.uuid4().hex})
        response = session.request(method, url, *args, **kwargs)
    except Exception as e:
        error_count += 1
        if error_count > max_errors:
            logger.error("error keeps recurring - quitting")
            exit(1)
        sleep_time = default_error_sleep * error_count
        logger.error(e)
        logger.warning(f"cant connect to indexer. sleeping {sleep_time}s")
        time.sleep(sleep_time)
        return _hoster_session_request(
            method, session, url, error_count=error_count, *args, **kwargs
        )
    return response


def process_block_url(session, block_url) -> None:
    response = _hoster_session_request("get", session, block_url)

    block_data = response.json()

    if block_data.get("status") == "sleep":
        retry_time = block_data["retry_at"]
        sleep_time = retry_time - time.time()
        logger.info(f"sleeping {sleep_time}...")
        time.sleep(sleep_time)
        return

    if BLOCK_KEY_CALLBACK_URL not in block_data:
        logger.error(
            f"skip crawl - no callback_url found! - key: {BLOCK_KEY_CALLBACK_URL}, block_data: {block_data}"
        )
    else:
        repos = run_block(block_data)
        _hoster_session_request(
            "PUT", session, url=block_data[BLOCK_KEY_CALLBACK_URL], json=repos
        )


def crawl(platform: ICrawler) -> Generator[List[dict], None, None]:
    """
    Run crawlers yielding results as it goes.
    Crawlers are restricted to ranges, or blocks, after which they will stop.

    :param platform: which platform to crawl, with what credentials
    """
    logger.debug(f"START block: {platform.type} - initial state: {platform.state}")
    for success, block_chunk, state in platform.crawl():
        if success:
            logger.info(f"got {len(block_chunk)} results from {platform} "
                        f"- first repo id: {next(iter(block_chunk), {}).get('id', None)}")
            yield block_chunk
        else:
            # right now we dont want to emit failures (via yield) because that will send empty results back
            # to the indexer, which can trigger a state reset (i.e. reached end, start over).
            # TODO deal with failures - what are they?
            pass
    logger.debug(f"END block: {platform.type} - final state: {platform.state}")


def run_block(block_data: dict) -> List[dict]:
    platform_data = block_data["hosting_service"]
    platform_type = platform_data["type"]
    api_url = platform_data["api_url"]
    api_key = platform_data.get("api_key", None)
    crawler_request_headers = platform_data["crawler_request_headers"]
    platform = platforms[platform_type](
        base_url=api_url,
        state=platforms[platform_type].state_from_block_data(block_data),
        api_key=api_key,
        user_agent=current_app.config["USER_AGENT"],
        extra_headers=crawler_request_headers
    )
    repos = []
    started_at = time.time()
    for block_chunk in crawl(platform):
        repos += block_chunk
    logger.info(
        f"{platform_type} - block yielded {len(repos)} results total, and took {time.time() - started_at}s"
    )
    return repos
