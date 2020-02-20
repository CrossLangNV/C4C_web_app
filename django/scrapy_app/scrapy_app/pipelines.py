import json
import os

import requests


class ScrapyAppPipeline(object):
    def __init__(self, unique_id, spider, *args, **kwargs):
        self.unique_id = unique_id
        self.spider = spider
        self.items = []
        self.django_api_url = os.environ['DJANGO_SCRAPING_API_URL']

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # this will be passed from django view
            unique_id=crawler.settings.get('unique_id'),
            spider=crawler.settings.get('spider')
        )

    def close_spider(self, spider):
        # save crawled data to django through API call
        item = {}
        item['unique_id'] = self.unique_id
        item['spider'] = self.spider
        item['data'] = json.dumps(self.items)
        requests.post(self.django_api_url + '/task/', json=item)

    def process_item(self, item, spider):
        self.items.append(item['data'])
        return item
