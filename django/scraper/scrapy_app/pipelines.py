import logging
import os
import uuid

import scrapy
from minio import Minio
from scrapy.pipelines.files import FilesPipeline

from scraper.scrapy_app.solr_call import solr_add

LOG = logging.getLogger("pysolr")
LOG.setLevel(logging.WARNING)


class ScrapyAppPipeline(FilesPipeline):
    def __init__(self, task_id, crawler, *args, **kwargs):
        self.task_id = task_id
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        if crawler.spider is None:
            spider_name = "default"
        else:
            spider_name = crawler.spider.name
        super().__init__(
            store_uri=os.environ['SCRAPY_FILES_FOLDER'] + 'files/' + spider_name, *args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # this will be passed from django view
            task_id=crawler.settings.get('task_id'),
            crawler=crawler
        )

    def get_media_requests(self, item, info):
        if 'pdf_docs' not in item:
            self.handle_document(item, info, [])
            return item
        else:
            for url in item['pdf_docs']:
                yield scrapy.Request(url)

    def file_path(self, request, response=None, info=None):
        return os.path.basename(request.url)

    def item_completed(self, results, item, info):
        file_results = [x for ok, x in results if ok]
        self.handle_document(item, info, file_results)
        return item

    def handle_document(self, item, info, file_results):
        item['task'] = self.task_id
        item['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url']))
        if item.get('doc_summary'):
            self.handle_document_summary(item)
        else:
            item['website'] = info.spider.name
            # GOAL: handle each file as a separate document: document id = doc url + file url
            # item['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url'] + file_result['url']))
            # FOR NOW: handle only first file of document: keep same id
            if len(file_results) > 0:
                file_result = file_results[0]
                # store in minio
                file_name = file_result['path']
                file_path = os.environ['SCRAPY_FILES_FOLDER'] + 'files/' + info.spider.name + "/" + file_name
                file_minio_path = self.minio_upload(file_path, file_name)
                item['file_url'] = file_result['url']
                item['file'] = file_minio_path

                # add/update and index document to Solr
                solr_add(core="documents", docs=[item])

    def minio_upload(self, file_path, file_name):
        minio = Minio(os.environ['MINIO_STORAGE_ENDPOINT'], access_key=os.environ['MINIO_ACCESS_KEY'],
                      secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
        minio.fput_object('local-media', file_name, file_path)
        return os.environ['MINIO_STORAGE_MEDIA_URL'] + '/' + file_name

    def handle_document_summary(self, item):
        solr_add(core="summaries", docs=[item])
