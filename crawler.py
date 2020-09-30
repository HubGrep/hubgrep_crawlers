import click
import logging
from lib.db import DB
from lib.platforms._generic import GenericCrawler
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
def add_platform(platform_type, base_url):
    db.add_platform(platform_type, base_url)

@cli.command()
def list_platforms():
    print(db.get_all_platforms())


@cli.command()
def crawl():
    for platform_id, platform_type, base_url, last_run in db.get_all_platforms():
        Crawler: GenericCrawler = platforms.get(platform_type, False)
        if Crawler:
            crawler = Crawler(platform_id, base_url)
            logger.info(f'starting {platform_type} crawler: {base_url}')
            for success, result_chunk in crawler.crawl():
                logger.info(f'got {len(result_chunk)} results from {base_url} ({platform_type})')
            
                db.add_or_update_results(result_chunk)
        else:
            logger.warning(f'could not find crawler class for type {platform_type}')
    pass


@cli.command()
def stats():
    click.echo(db.stats())

if __name__ == '__main__':
    cli()
