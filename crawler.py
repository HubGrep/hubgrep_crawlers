import click
import logging
from lib.db import DB
from lib.platforms._generic import GenericIndexer
from lib.platforms import platforms

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

db = DB()


@click.group()
def cli():
    pass


@cli.command()
def db_create():
    db.create()


@cli.command()
def db_drop():
    if click.confirm('delete database?', default=False):
        db.drop()


@cli.command()
def db_init():
    db.init()


@cli.command()
@click.argument('platform_type', type=click.Choice(platforms.keys()))
@click.argument('base_url')
@click.option('--auth_data', default=None)
def add_platform(platform_type, base_url, auth_data):
    db.platform_add(platform_type, base_url, auth_data)


@cli.command()
def list_platforms():
    for platform in db.platform_get_all():
        import json
        click.echo(f'{platform}, {json.dumps(platform.state)}')

@cli.command()
@click.argument('platform_type', type=click.Choice(platforms.keys()))
@click.argument('base_url')
def reset_state_platform(platform_type, base_url):
    if click.confirm(
        f'really reset indexer state for {platform_type}/{base_url}?',
            default=False):
        platform = db.platform_get(platform_type, base_url)
        db.platform_update_state(platform._id, None)


@cli.command()
@click.argument('platform_type', type=click.Choice(platforms.keys()))
@click.argument('base_url')
def del_platform(platform_type, base_url):
    if click.confirm(
        f'really delete {platform_type}/{base_url}? this will delete all collected repos too!',
            default=False):
        db.platform_delete(platform_type, base_url)


@cli.command()
@click.option('--platform-base-url', default=None)
@click.option('--platform', default=None)
def crawl(platform_base_url, platform):
    all_platforms = db.platform_get_all(
            platform=platform,
            base_url=platform_base_url)
    logger.info(f'crawling {", ".join(str(p) for p in all_platforms)}')

    for platform in all_platforms:
        logger.info(f'starting {platform}')
        for success, result_chunk, state in platform.crawl(
                state=platform.state):
            if success:
                logger.info(f'got {len(result_chunk)} results from {platform}')
                db.results_add_or_update(result_chunk)
                db.platform_update_state(platform._id, state)
        db.platform_update_state(platform._id, None)
    logger.info(f'finished {", ".join(str(p) for p in all_platforms)}')

@cli.command()
@click.argument('query_str')
@click.option('--limit', type=click.INT)
def query(query_str, limit):
    for line in db.query(query_str, limit):
        base_url = line[0]
        name = line[1]
        owner_name = line[2]
        description = line[3]
        rank = line[4]
        click.echo(click.style(f'{owner_name} - {name}', bold=True) + f' @{base_url} -- RANK {rank}')
        click.echo(f'\t{description}')


@cli.command()
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


if __name__ == '__main__':
    cli()
