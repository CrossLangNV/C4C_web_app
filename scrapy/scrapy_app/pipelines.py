import os
import uuid
from urllib.parse import urlparse

import scrapy
from scrapy.pipelines.files import FilesPipeline

from scrapy_app.solr_call import solr_add, solr_add_file


class ScrapyAppPipeline(FilesPipeline):
    def __init__(self, task_id, *args, **kwargs):
        self.task_id = task_id
        self.django_api_url = os.environ['DJANGO_SCRAPING_API_URL']

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # this will be passed from django view
            task_id=crawler.settings.get('task_id')
        )

    def get_media_requests(self, item, info):
        if not 'pdf_docs' in item:
            self.handle_document(item, info)
            return item
        else:
            for url in item['pdf_docs']:
                yield scrapy.Request(url)

    def file_path(self, request, response=None, info=None):
        return 'files/' + os.path.basename(urlparse(request.url).path)

    def item_completed(self, results, item, info):
        self.handle_document(item, info)
        file_paths = [x['path'] for ok, x in results if ok]
        for file in file_paths:
            pdf_id = str(uuid.uuid5(uuid.NAMESPACE_URL, file['url']))
            solr_add_file('files', file, pdf_id, file['url'], item['id'])

        return item

    def handle_document(self, item, info):
        item['task'] = self.task_id
        item['website'] = info.spider.name
        item['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url']))
        # add/update and index item to Solr
        solr_add(core="documents", docs=[item])
