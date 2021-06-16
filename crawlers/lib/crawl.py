"""
Main crawler processing.
"""
import logging
import requests
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from time import sleep
from typing import List, Generator
from flask import current_app

from crawlers.constants import CRAWLER_IS_RUNNING_ENV_KEY
from crawlers.lib.platforms.i_crawler import ICrawler
from crawlers.lib.platforms import platforms

logger = logging.getLogger(__name__)


def crawl(platform: ICrawler) -> Generator[List[dict], None, None]:
    """
    Run crawlers yielding results as it goes.
    Crawlers are restricted to ranges, or blocks, after which they will stop.

    :param platform: which platform to crawl, with what credentials
    """
    logger.info(f'crawling platform: {platform} - initial state: {platform.state}')
    for success, result_chunk, state in platform.crawl(state=platform.state):
        if success:
            logger.info(f'got {len(result_chunk)} results from {platform}')

            yield result_chunk
        else:
            # TODO deal with failures - what are they?
            pass

    logger.info(f'crawling complete: {platform} - final state: {platform.state}')


def _run_job(job_data: dict) -> List[dict]:
    # platform_key, api_url, headerstw
    platform_key = "github"  # TODO indexer should give us -> data["platform_key"]
    api_url = "https://api.github.com"  # job_data["api_url"]
    api_auth_data = {"access_token": "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"}  # job_data["headers"]
    platform = platforms[platform_key](base_url=api_url,
                                       state=platforms[platform_key].state_from_job_data(job_data),
                                       auth_data=api_auth_data,
                                       user_agent=current_app.config["CRAWLER_USER_AGENT"])
    repos = []
    started_at = time.time()
    for chunk in crawl(platform):
        repos += chunk
    logger.debug(f'job yielded {len(repos)} results total, and took {time.time() - started_at}s')
    return repos


def run_crawler():
    job_url = current_app.config["JOB_URL"]
    sleep_no_job = current_app.config["CRAWLER_SLEEP_NO_JOB"]

    session = requests.session()
    retries = Retry(total=3,
                    backoff_factor=10,
                    status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    logger.debug(f'initiate crawler loop - requesting @ {job_url}')
    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "1"
    while os.environ[CRAWLER_IS_RUNNING_ENV_KEY] == "1":
        response = session.request(
            method="GET",
            url=job_url)
        if not response.ok:
            logger.debug(f'JOB REQUEST FAILED WITH {response.status_code} - SLEEP FOR {sleep_no_job}s')
            sleep(sleep_no_job)
        else:
            job_data = response.json()
            if job_data.get("sleep", False):
                sleep(job_data["sleep"])
            else:
                repos = _run_job(job_data)
                session.request(
                    method="POST",
                    url=job_data["callback_url"],
                    json=repos
                )

        return
