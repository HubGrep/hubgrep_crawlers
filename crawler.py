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
    db.platform_add(platform_type, base_url)


@cli.command()
def list_platforms():
    click.echo(db.platforms_get_all())


@cli.command()
@click.argument('platform_type', type=click.Choice(platforms.keys()))
@click.argument('base_url')
def del_platform(platform_type, base_url):
    if click.confirm(
        f'really delete {platform_type}/{base_url}? this will delete all collected repos too!',
            default=False):
        db.platform_delete(platform_type, base_url)


@cli.command()
@click.option('--platform-base-url')
@click.option('--platform')
def crawl(platform_base_url, platform):
    for platform_id, platform_type, base_url, last_run, state in db.platform_get_all():
        Crawler: GenericCrawler = platforms.get(platform_type, False)
        if Crawler:
            crawler = Crawler(platform_id, base_url)
            if not platform_base_url or platform_base_url == base_url:
                if not platform or platform_type == platform:
                    logger.info(
                        f'starting {crawler}')
                    for success, result_chunk, state in crawler.crawl(state=state):
                        logger.info(
                            f'got {len(result_chunk)} results from {crawler}')
                        db.results_add_or_update(result_chunk)
                        db.platform_update_state(platform_id, state)

                else:
                    logger.warning(f'skipping {base_url}')
            else:
                logger.warning(f'skipping {base_url}')
        else:
            logger.warning(
                f'could not find crawler class for type {platform_type}')
    pass



@cli.command()
def stats():
    click.echo(db.stats())


if __name__ == '__main__':
    cli()
