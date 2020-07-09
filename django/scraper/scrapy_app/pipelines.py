import logging
import os
import uuid
from datetime import datetime

import requests
import scrapy
from minio import Minio
from scrapy.pipelines.files import FilesPipeline
from scrapy import signals

from scraper.scrapy_app.minio_call import S3ItemExporter

LOG = logging.getLogger("pysolr")
LOG.setLevel(logging.WARNING)

FILE_LOG = logging.getLogger("scrapy.pipelines.files")
FILE_LOG.setLevel(logging.ERROR)


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
        pipeline = cls(
            # this will be passed from celery task
            task_id=crawler.settings.get('celery_id'),
            crawler=crawler
        )
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.exporter = S3ItemExporter(spider.name)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()

    # This method is called once per downloaded item. It returns the download path of the file originating from the specified response.
    # You can override this method to customize the download path of each file.
    def file_path(self, request, response=None, info=None):
        return os.path.basename(request.url)

    def check_redirect(self, url):
        headers = {'Accept': 'application/xhtml+xml,text/html',
                   'Accept-Language': 'eng'}
        response = requests.head(url, headers=headers)
        if response.status_code == 303:
            url = response.headers["Location"]
        return url

    # The pipeline will get the URLs of the images to download from the item.
    # In order to do this, you can override the get_media_requests() method and return a Request for each file URL.
    # Those requests will be processed by the pipeline and, when they have finished downloading, the results will be sent to the item_completed() method,
    def get_media_requests(self, item, info):
        if 'html_docs' in item and not 'content_html' in item:
            for url in item['html_docs']:
                headers = {'Accept': ['application/xhtml+xml',
                                      'text/html'], 'Accept-Language': 'eng'}
                yield scrapy.Request(self.check_redirect(url), headers=headers)

        if 'pdf_docs' in item:
            for url in item['pdf_docs']:
                yield scrapy.Request(url)

    # The FilesPipeline.item_completed() method called when all file requests for a single item have completed (either finished downloading, or failed for some reason).
    def item_completed(self, results, item, info):
        file_results = [x for ok, x in results if ok]
        self.handle_document(item, info, file_results)
        return item

    def handle_document(self, item, info, file_results):
        item['task'] = self.task_id
        item['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url']))
        self.logger.debug("HANDLING_DOC: %s, %s", item['id'], item['url'])

        self.handle_dates(item)
        item['website'] = info.spider.name
        # GOAL: handle each file as a separate document: document id = doc url + file url
        # item['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url'] + file_result['url']))
        # FOR NOW: handle only first file of document: keep same id
        self.logger.debug("FILERESULTS: %s", file_results)
        if len(file_results) > 0:
            file_result = file_results[0]
            file_name = file_result['path']
            file_path = os.environ['SCRAPY_FILES_FOLDER'] + \
                'files/' + info.spider.name + "/" + file_name
            if file_result['url'].startswith('http://publications.europa.eu/resource/cellar/'):
                f = open(file_path, "r")
                item['content_html'] = f.read()
                self.logger.info(
                    "GOT HTML FROM CELLAR for ITEM: %s", item['url'])
            else:
                # store in minio
                file_minio_path = self.minio_upload(file_path, file_name)
                item['file_url'] = file_result['url']
                item['file'] = file_minio_path

        # Export item to minio jsonl file
        if 'doc_summary' not in item:
            self.exporter.export_item(item)

    def handle_dates(self, item):
        if item.get('date'):
            if isinstance(item['date'], datetime):
                item['date'] = item['date'].isoformat() + "Z"
        date_field_lists = ['dates', 'amendments_from', 'amendments_to']
        for field in date_field_lists:
            if item.get(field):
                string_dates = []
                for some_date in item[field]:
                    if isinstance(some_date, datetime):
                        string_dates.append(some_date.isoformat() + "Z")
                item[field] = string_dates

    def minio_upload(self, file_path, file_name):
        minio = Minio(os.environ['MINIO_STORAGE_ENDPOINT'], access_key=os.environ['MINIO_ACCESS_KEY'],
                      secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
        minio.fput_object('local-media', file_name, file_path)
        return os.environ['MINIO_STORAGE_MEDIA_URL'] + '/' + file_name
