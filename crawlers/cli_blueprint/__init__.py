"""
CLI tool for crawler interactions.
"""
import os
import logging
from flask import Blueprint
from dotenv import load_dotenv

from crawlers.constants import CRAWLER_IS_RUNNING_ENV_KEY
from crawlers.lib.crawl import run_crawler

load_dotenv()

logger = logging.getLogger(__name__)

cli_bp = Blueprint("cli", __name__)


@cli_bp.cli.command(
    help=f'Initiate automatic crawler. Looks for job_url @ env-var: HUBGREP_CRAWLERS_JOB_URL.')
def crawl_start():
    run_crawler()


@cli_bp.cli.command(help="Stop automatic crawlers.")
def crawl_stop():
    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "0"
