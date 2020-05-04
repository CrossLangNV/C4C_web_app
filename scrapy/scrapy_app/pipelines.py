import logging
import os
import uuid
from urllib.parse import urlparse

import scrapy
from scrapy.pipelines.files import FilesPipeline

from scrapy_app.solr_call import solr_add, solr_add_file


class ScrapyAppPipeline(FilesPipeline):
    def __init__(self, task_id, crawler, *args, **kwargs):
        self.task_id = task_id
        self.crawler = crawler
        self.django_api_url = os.environ['DJANGO_SCRAPING_API_URL']
        self.logger = logging.getLogger(__name__)
        super().__init__(
            store_uri=os.environ['SCRAPY_FILES_FOLDER'] + 'files/' + crawler.spider.name, *args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # this will be passed from django view
            task_id=crawler.settings.get('task_id'),
            crawler=crawler
        )

    def get_media_requests(self, item, info):
        if 'pdf_docs' not in item:
            self.handle_document(item, info)
            return item
        else:
            for url in item['pdf_docs']:
                yield scrapy.Request(url)

    def file_path(self, request, response=None, info=None):
        return os.path.basename(request.url)

    def item_completed(self, results, item, info):
        self.handle_document(item, info)
        self.logger.info(results)
        file_results = [x for ok, x in results if ok]
        for file_result in file_results:
            pdf_id = str(uuid.uuid5(uuid.NAMESPACE_URL, file_result['url']))
            file = open(os.environ['SCRAPY_FILES_FOLDER'] +
                        'files/' + info.spider.name + "/" + file_result['path'], mode='rb')
            solr_add_file('files', file, pdf_id,
                          file_result['url'], item['id'])

        return item

    def handle_document(self, item, info):
        item['task'] = self.task_id
        item['website'] = info.spider.name
        item['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url']))
        # add/update and index item to Solr
        solr_add(core="documents", docs=[item])
