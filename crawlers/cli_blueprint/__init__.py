"""
CLI tool for crawler interactions.
"""

import os
import logging
import click
from typing import List
from urllib.parse import urljoin
from flask import Blueprint, current_app
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from crawlers.constants import CRAWLER_IS_RUNNING_ENV_KEY
from crawlers.lib.crawl import process_block_url


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
    indexer_api_key = current_app.config.get("INDEXER_API_KEY", None)
    if indexer_api_key:
        session.headers.update({"Authorization": f"Basic {indexer_api_key}"})
    return session


# todo: make list command


@cli_bp.cli.command(help="Start automatic crawler against a specific block_url.")
@click.argument("block_url")
def crawl_block_url(block_url: str):
    session = get_requests_session()

    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "1"
    while os.environ[CRAWLER_IS_RUNNING_ENV_KEY]:
        process_block_url(session, block_url)


@cli_bp.cli.command(help="Start automatic crawler against specific hosters.")
@click.argument("hoster_api_domains", nargs=-1)
def crawl_hoster(hoster_api_domains: List[str] = None):
    hoster_api_domains = list(hoster_api_domains)
    indexer_url = current_app.config["INDEXER_URL"]
    session = get_requests_session()
    block_urls = []

    # gets a list of all hosters from the indexer
    response = session.get(urljoin(indexer_url, "api/v1/hosters"))
    response.raise_for_status()
    if hoster_api_domains:
        for hoster in response.json():
            # todo: maybe this should match without protocol as well?
            domain = hoster["api_url"]
            if domain in hoster_api_domains:
                logger.debug(f"adding hoster: {hoster}")
                block_urls.append(
                    urljoin(indexer_url, f"api/v1/hosters/{hoster['id']}/block")
                )
                hoster_api_domains.remove(domain)
        # left over api domains means the indexer doesnt know them
        if hoster_api_domains:
            raise KeyError(f"could not find hosters: {hoster_api_domains} in indexer!")

    else:
        raise KeyError("specify at least one hoster api url!")

    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "1"
    while os.environ[CRAWLER_IS_RUNNING_ENV_KEY]:
        for url in block_urls:
            process_block_url(session, url)


@cli_bp.cli.command(help="Start automatic crawler with a hoster type (such as github)")
@click.argument("platform-type")
def crawl_type(platform_type: str):
    indexer_url = current_app.config["INDEXER_URL"]
    session = get_requests_session()

    block_url = urljoin(
        indexer_url, f"api/v1/hosters/{platform_type}/loadbalanced_block"
    )

    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "1"
    while os.environ[CRAWLER_IS_RUNNING_ENV_KEY]:
        process_block_url(session, block_url)


@cli_bp.cli.command(help="Stop automatic crawlers, after finishing the current block.")
def crawl_stop():
    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "0"
