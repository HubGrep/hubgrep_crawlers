import logging
import time
from urllib.parse import urljoin

from iso8601 import iso8601
from lib.platforms._generic import GenericResult, GenericCrawler

logger = logging.getLogger(__name__)

# https://developer.github.com/v3/search/

class GiteaResult(GenericResult):
    def __init__(self, platform_id, search_result_item):
        name = search_result_item['name']
        owner_name = search_result_item['owner']['login']
        description = search_result_item['description'] or '?'
        last_commit = iso8601.parse_date(search_result_item['updated_at'])
        created_at = iso8601.parse_date(search_result_item['created_at'])
        language = '?'
        license_dict = search_result_item.get('license')
        license = license_dict.get('name', None) if license_dict else None

        html_url = search_result_item['html_url']

        super().__init__(platform_id=platform_id,
                         name=name,
                         description=description,
                         html_url=html_url,
                         owner_name=owner_name,
                         last_commit=last_commit,
                         created_at=created_at,
                         language=language,
                         license=license)


class GiteaSearch(GenericCrawler):
    name = 'gitea'

    def __init__(self, platform_id, base_url):
        super().__init__(
            platform_id=platform_id,
            base_url=base_url,
            path='api/v1/repos/search')
        self.request_url = urljoin(self.base_url, self.path)

    def crawl(self, state=None):
        if not state:
            page = 1
        else:
            page = state.get('page', False)
            if not page:
                logger.warning(f'{self} broken state, defaulting to start')
        results = True
        while results:
            params = dict(
                sort='created',
                limit=50,
                page=page
            )
            try:
                response = self.requests.get(self.request_url, params=params)
            except Exception as e:
                logger.error(e)
                return False, e
            result = response.json()
            results = [GiteaResult(self.platform_id, item) for item in result['data']]
            yield True, results
            page += 1
            time.sleep(.5)

