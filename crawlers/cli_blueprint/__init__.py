"""
CLI tool for crawler interactions.
"""

import os
import logging
import click
from urllib.parse import urljoin
from flask import Blueprint, current_app
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from crawlers.constants import CRAWLER_IS_RUNNING_ENV_KEY, BLOCK_KEY_CALLBACK_URL
from crawlers.lib.crawl import run_block

load_dotenv()

logger = logging.getLogger(__name__)

cli_bp = Blueprint("cli", __name__)


def get_requests_session():
    import requests

    session = requests.session()
    retries = Retry(
        total=3, backoff_factor=10, status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


@cli_bp.cli.command(help="Start automatic crawler with a hoster type (such as github) or against a specific block_url.")
@click.argument("platform-types", nargs=-1)
@click.option("-u", "--block-url", "block_url", nargs=1)
def crawl(platform_types: list = None, block_url: str = None):
    indexer_url = current_app.config["INDEXER_URL"]
    session = get_requests_session()
    block_urls = []

    if platform_types and len(platform_types) > 0:
        # gets a list of all hosters from the indexer
        response = session.get(urljoin(indexer_url, "api/v1/hosters"))
        response.raise_for_status()

        for hoster in response.json():
            if hoster["type"] in platform_types:
                logger.debug(f'adding hoster: {hoster}')
                block_urls.append(urljoin(indexer_url, f"api/v1/hosters/{hoster['id']}/block"))

    elif block_url:
        logger.debug(f"run crawler against: {block_url}")
        block_urls.append(block_url)
    else:
        raise KeyError('specify at least one option: "-platform-types" or "-job-url"')

    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "1"
    while os.environ[CRAWLER_IS_RUNNING_ENV_KEY]:
        for url in block_urls:
            response = session.get(url)
            block_data = response.json()
            if BLOCK_KEY_CALLBACK_URL not in block_data:
                logger.error(
                    f"skip crawl - no callback_url found! - key: {BLOCK_KEY_CALLBACK_URL}, block_data: {block_data}")
            else:
                repos = run_block(block_data)
                session.request(method="PUT", url=block_data[BLOCK_KEY_CALLBACK_URL], json=repos)


@cli_bp.cli.command(help="Stop automatic crawlers, after finishing the current block.")
def crawl_stop():
    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "0"
