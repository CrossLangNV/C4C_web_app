import json
import os

import requests


class ScrapyAppPipeline(object):
    def __init__(self, task_id, *args, **kwargs):
        self.task_id = task_id
        self.django_api_url = os.environ['DJANGO_SCRAPING_API_URL']

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # this will be passed from django view
            task_id=crawler.settings.get('task_id')
        )

    def process_item(self, item, spider):
        # save crawled data to django through API call
        item['task'] = self.task_id
        item['data'] = json.dumps(item['data'])
        requests.post(self.django_api_url + '/task/' + self.task_id + '/', json=item)
        return item
