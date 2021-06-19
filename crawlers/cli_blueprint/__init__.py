"""
CLI tool for crawler interactions.
"""

import os
import logging
import click
from flask import Blueprint
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from time import sleep
from crawlers.constants import CRAWLER_IS_RUNNING_ENV_KEY
from crawlers.lib.crawl import run_crawler
from crawlers.lib.crawl import _run_job

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


@cli_bp.cli.command(help="")
@click.argument("platform-types", nargs=-1)
def crawl_start(platform_types):
    indexer_url = os.environ["HUBGREP_INDEXER_URL"]
    session = get_requests_session()

    # get a list of all hosters
    response = session.get(indexer_url + "api/v1/hosters")
    response.raise_for_status()
    hosters = [hoster for hoster in response.json() if hoster["type"] in platform_types]

    logger.info(f"start crawling on {hosters}")

    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "1"
    while os.environ[CRAWLER_IS_RUNNING_ENV_KEY]:
        for hoster in hosters:
            response = session.get(indexer_url + f"api/v1/hosters/{hoster['id']}/block")
            job_data = response.json()

            repos = _run_job(job_data)
            session.request(method="POST", url=job_data["callback_url"], json=repos)


@cli_bp.cli.command(help="Stop automatic crawlers.")
def crawl_stop():
    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "0"
