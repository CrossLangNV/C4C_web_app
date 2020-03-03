import os
import uuid
from urllib.request import urlopen

from scrapy_app.solr_call import solr_add, solr_add_file


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
        item['website'] = spider.name
        # generate UUID (version 5, see https://tools.ietf.org/html/rfc4122#section-4.3) based on url
        item['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url']))
        # add/update and index item to Solr
        solr_add(core="documents", docs=[item])
        for url in item['pdf_docs']:
            pdf_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
            file = urlopen(url)
            file.name = os.path.basename(url)
            solr_add_file('files', file, pdf_id, url, item['id'])

        return item
