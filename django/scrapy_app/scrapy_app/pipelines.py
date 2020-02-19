import json
import os

import requests


class ScrapyAppPipeline(object):
    def __init__(self, unique_id, *args, **kwargs):
        self.unique_id = unique_id
        self.items = []
        self.django_api_url = os.environ['DJANGO_SCRAPING_API_URL']

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            unique_id=crawler.settings.get('unique_id'),  # this will be passed from django view
        )

    def close_spider(self, spider):
        # save crawled data to django through API call
        item = {}
        item['unique_id'] = self.unique_id
        item['data'] = json.dumps(self.items)
        requests.post(self.django_api_url + '/task/', json=item)

    def process_item(self, item, spider):
        self.items.append(item['data'])
        return item
