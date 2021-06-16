"""
CLI tool for crawler and database interactions.

Note that crawling via the CLI will store results in the database to make it
easier to test and reason about the crawlers from a localdev perspective.
"""
import os
import sys
import json
import click
import logging
from flask import Blueprint
from dotenv import load_dotenv

from crawlers.constants import CRAWLER_IS_RUNNING_ENV_KEY
from crawlers.lib.db import DB
from crawlers.lib.crawl import crawl as _crawl, run_crawler
from crawlers.lib.platforms import platforms
from crawlers.lib.util.stream_array import StreamArray

load_dotenv()

logger = logging.getLogger(__name__)

db = DB()

cli_bp = Blueprint("cli", __name__)


@cli_bp.cli.command()
def db_create():
    db.create()


@cli_bp.cli.command()
def db_drop():
    if click.confirm('delete database?', default=False):
        db.drop()


@cli_bp.cli.command()
def db_init():
    db.init()


@cli_bp.cli.command()
@click.argument('platform_type', type=click.Choice(platforms.keys()))
@click.argument('base_url')
@click.option('--auth_data', default=None)
def add_platform(platform_type, base_url, auth_data):
    print("ADD...", auth_data)
    auth_json = None
    if auth_data:
        auth_json = json.loads(auth_data)
    db.platform_add(platform_type, base_url, auth_json)


@cli_bp.cli.command()
def list_platforms():
    for platform in db.platform_get_all():
        click.echo(f'{platform}, {json.dumps(platform.state)}')


@cli_bp.cli.command()
@click.argument('platform_type', type=click.Choice(platforms.keys()))
@click.argument('base_url')
def reset_state_platform(platform_type, base_url):
    if click.confirm(
            f'really reset indexer state for {platform_type}/{base_url}?',
            default=False):
        platform = db.platform_get(platform_type, base_url)
        db.platform_update_state(platform._id, None)


@cli_bp.cli.command()
@click.argument('platform_type', type=click.Choice(platforms.keys()))
@click.argument('base_url')
def del_platform(platform_type, base_url):
    if click.confirm(
            f'really delete {platform_type}/{base_url}? this will delete all collected repos too!',
            default=False):
        db.platform_delete(platform_type, base_url)


@cli_bp.cli.command(help="For localdev - collect and store repo data in local db.")
@click.option('--platform-base-url', default=None)
@click.option('--platform', type=click.Choice(list(platforms.keys()) + [None]))
def crawl(platform_base_url, platform):
    all_platforms = db.platform_get_all(
        platform=platform,
        base_url=platform_base_url)
    print(all_platforms)
    _crawl(platforms=all_platforms, store_state=True, store_results=True)


@cli_bp.cli.command(
    help=f'Initiate automatic crawler. Looks for job_url @ env-var: HUBGREP_CRAWLERS_JOB_URL.')
def crawl_start():
    run_crawler()


@cli_bp.cli.command(help="Stop automatic crawlers.")
def crawl_stop():
    os.environ[CRAWLER_IS_RUNNING_ENV_KEY] = "0"


@cli_bp.cli.command()
@click.argument('query_str')
@click.option('--limit', type=click.INT)
def query(query_str, limit):
    for line in db.query(query_str, limit):
        base_url = line[0]
        name = line[1]
        owner_name = line[2]
        description = line[3]
        rank = line[4]
        click.echo(click.style(
            f'{owner_name} - {name}', bold=True) +
                   f' @{base_url} -- RANK {rank}')
        click.echo(f'\t{description}')


@cli_bp.cli.command(help="Exports data collected by crawlers as json.")
@click.argument('path', type=click.Path(dir_okay=False,
                                        file_okay=True, exists=False))
@click.option('--platform-base-url', default=None)
def export(path, platform_base_url):
    def date_converter(o):
        import datetime
        if isinstance(o, datetime.datetime):
            return datetime.datetime.isoformat(o)

    with (open(path, 'w') if path != '-' else sys.stdout) as f:
        stream_array = StreamArray(db.repo_get_all(platform_base_url))
        for chunk in json.JSONEncoder(default=date_converter).iterencode(stream_array):
            f.write(chunk)


@cli_bp.cli.command()
def stats():
    _format = '%-15s%-30s%s'
    click.echo(
        click.style(
            _format %
            ('type',
             'base_url',
             'repos'),
            bold=True))
    for stat in db.stats():
        click.echo(_format % stat)
