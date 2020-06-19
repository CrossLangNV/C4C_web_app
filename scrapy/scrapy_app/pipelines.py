import requests
import logging
import os
import uuid

import scrapy
from minio import Minio
from minio.error import ResponseError

from scrapy.pipelines.files import FilesPipeline

from scrapy_app.solr_call import solr_add

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
        if 'html_docs' in item:
            for url in item['html_docs']:
                headers = {'Accept': ['application/xhtml+xml',
                                      'text/html'], 'Accept-Language': 'eng'}
                yield scrapy.Request(self.check_redirect(url), headers=headers)
        if 'pdf_docs' in item:
            for url in item['pdf_docs']:
                yield scrapy.Request(url)
        if 'pdf_docs' not in item and 'html_docs' not in item:
            self.handle_document(item, info, [])
            return item

    # The FilesPipeline.item_completed() method called when all file requests for a single item have completed (either finished downloading, or failed for some reason).
    def item_completed(self, results, item, info):
        file_results = [x for ok, x in results if ok]
        self.handle_document(item, info, file_results)
        return item

    def handle_document(self, item, info, file_results):
        item['task'] = self.task_id
        item['id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, item['url']))
        self.logger.debug("HANDLING_DOC: %s", item)
        if item.get('doc_summary'):
            self.handle_document_summary(item)
        else:
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
                else:
                    # store in minio
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
        del item['doc_summary']
        solr_add(core="summaries", docs=[item])
