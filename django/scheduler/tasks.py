from __future__ import absolute_import, unicode_literals

import logging
import os
import shutil
import time
from urllib.parse import quote
from io import BytesIO

import pysolr

from datetime import datetime, timedelta
import requests
from celery import shared_task
from django.db.models.functions import Length
from jsonlines import jsonlines
from minio import Minio, ResponseError
from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from tika import parser
from twisted.internet import reactor

from searchapp.datahandling import score_documents
from searchapp.models import Website, Document, Attachment, AcceptanceState
from searchapp.solr_call import solr_search, solr_search_document_id_sorted, solr_search_website_sorted, solr_search_website_paginated, solr_search_website_with_content

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))


@shared_task
def full_service_task(website_id):
    website = Website.objects.get(pk=website_id)
    logger.info("Full service for WEBSITE: %s",  website.name)
    scrape_website_task(website_id, delay=False)
    sync_scrapy_to_solr_task(website_id)
    parse_content_to_plaintext_task(website_id)
    sync_documents_task(website_id)
    score_documents_task(website_id)
    logger.info("Full service for WEBSITE (DONE): %s", website.name)


@shared_task
def export_documents(website_ids=None):
    websites = Website.objects.all()
    if website_ids:
        websites = Website.objects.filter(pk__in=website_ids)
    for website in websites:
        page_number = 0
        rows_per_page = 250
        cursor_mark = "*"
        # Make sure solr index is updated
        core = 'documents'
        requests.get(os.environ['SOLR_URL'] +
                     '/' + core + '/update?commit=true')
        if not os.path.exists(workpath + '/export/jsonl/' + website.name):
            os.makedirs(workpath + '/export/jsonl/' + website.name)
        # select all records for website
        q = 'website:' + website.name
        if website.name.lower() == 'eurlex':
            # only documents with content_html for eurlex
            q += ' AND content_html:*'
        client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
        options = {'rows': rows_per_page, 'start': page_number,
                   'cursorMark': cursor_mark, 'sort': 'id asc'}
        documents = client.search(q, **options)
        for document in documents:
            with jsonlines.open(workpath + '/export/jsonl/' + website.name + '/doc_' + document['id'] + '.jsonl',
                                mode='w') as f:
                f.write(document)
                # get acceptance state from django model
                acceptance_state_qs = AcceptanceState.objects.filter(document__id=document['id'],
                                                                     probability_model='auto classifier')
                if acceptance_state_qs:
                    acceptance_state = acceptance_state_qs[0]
                    classifier_score = acceptance_state.accepted_probability
                    classifier_status = acceptance_state.value
                    classifier_index = acceptance_state.accepted_probability_index
                    classifier = {'classifier_status': classifier_status, 'classifier_score': classifier_score,
                                  'classifier_index': classifier_index}
                    f.write(classifier)

    # create zip file for all .jsonl files
    zip_destination = workpath + '/export/' + export_documents.request.id
    shutil.make_archive(zip_destination, 'zip', workpath + '/export/jsonl')

    # upload zip to minio
    minio_client = Minio(os.environ['MINIO_STORAGE_ENDPOINT'], access_key=os.environ['MINIO_ACCESS_KEY'],
                         secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
    try:
        minio_client.make_bucket('export')
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass
    except ResponseError as err:
        raise
    minio_client.fput_object(
        'export', export_documents.request.id + '.zip', zip_destination + '.zip')


@shared_task
def export_delete(task_id):
    # delete export jsonl contents
    for filename in os.listdir(workpath + '/export/jsonl'):
        file_path = os.path.join(workpath + '/export/jsonl', filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error('Failed to delete %s. Reason: %s' %
                         (file_path, e))
    # delete zip with given task id
    os.remove(workpath + '/export/' + task_id + '.zip')


@shared_task
def score_documents_task(website_id):
    # lookup documents for website and score them
    website = Website.objects.get(pk=website_id)
    logger.info("Scoring documents with WEBSITE: " + website.name)
    solr_documents = solr_search_website_with_content(
        'documents', website.name)
    use_pdf_files = True
    if website.name.lower() == 'eurlex':
        use_pdf_files = False
    score_documents(website.name, solr_documents, use_pdf_files)


@shared_task
def sync_documents_task(website_id):
    # lookup documents for website and sync them
    website = Website.objects.get(pk=website_id)
    logger.info("Syncing documents with WEBSITE: " + website.name)
    # query Solr for available documents and sync with Django
    solr_documents = solr_search_website_sorted(
        core='documents', website=website.name.lower())
    for solr_doc in solr_documents:
        solr_doc_date = solr_doc.get('date', [datetime.now()])[0]
        solr_doc_date_last_update = solr_doc.get(
            'date_last_update', datetime.now())
        data = {
            "author": solr_doc.get('author', [''])[0][:20],
            "celex": solr_doc.get('celex', [''])[0][:20],
            "consolidated_versions": ','.join(x.strip() for x in solr_doc.get('consolidated_versions', [''])),
            "date": solr_doc_date,
            "date_last_update": solr_doc_date_last_update,
            "eli": solr_doc.get('eli', [''])[0],
            "file_url": solr_doc.get('file_url', [None])[0],
            "status": solr_doc.get('status', [''])[0][:100],
            "summary": ''.join(x.strip() for x in solr_doc.get('summary', [''])),
            "title": solr_doc.get('title', [''])[0][:1000],
            "title_prefix": solr_doc.get('title_prefix', [''])[0],
            "type": solr_doc.get('type', [''])[0],
            "url": solr_doc['url'][0],
            "various": ''.join(x.strip() for x in solr_doc.get('various', [''])),
            "website": website,
        }
        Document.objects.update_or_create(id=solr_doc["id"], defaults=data)
    # safe delete documents that have not been updated in a while
    how_many_days = 30
    docs = Document.objects.filter(
        date_last_update__lte=datetime.now()-timedelta(days=how_many_days))
    for doc in docs:
        doc.delete()


@shared_task
def scrape_website_task(website_id, delay=True):
    # lookup website and start scraping
    website = Website.objects.get(pk=website_id)
    logger.info("Scraping with WEBSITE: " + website.name)
    spiders = [{"id": "bis"}, {"id": "eiopa"}, {"id": "esma"},
               {"id": "eurlex", "type": "directives"},
               {"id": "eurlex", "type": "decisions"},
               {"id": "eurlex", "type": "regulations"},
               {"id": "fsb"}, {"id": "srb"},
               {"id": "eba", "type": "guidelines"},
               {"id": "eba", "type": "recommendations"},
               ]
    for spider in spiders:
        if spider['id'].lower() == website.name.lower():
            if 'type' not in spider:
                spider['type'] = ''
            date_start = None
            date_end = None
            # schedule scraping task
            if spider['id'] == "eurlex":
                for year in range(1951, datetime.now().year + 1):
                    date_start = "0101" + str(year)
                    date_end = "3112" + str(year)
                    if delay:
                        launch_crawler.delay(
                            spider['id'], spider['type'], date_start, date_end)
                    else:
                        launch_crawler(
                            spider['id'], spider['type'], date_start, date_end)
            else:
                if delay:
                    launch_crawler.delay(
                        spider['id'], spider['type'], date_start, date_end)
                else:
                    launch_crawler(
                        spider['id'], spider['type'], date_start, date_end)


@shared_task
def launch_crawler(spider, spider_type, date_start, date_end):
    scrapy_settings_path = 'scraper.scrapy_app.settings'
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', scrapy_settings_path)
    settings = get_project_settings()
    settings['celery_id'] = launch_crawler.request.id
    runner = CrawlerRunner(settings=settings)
    d = runner.crawl(spider, spider_type=spider_type,
                     spider_date_start=date_start,
                     spider_date_end=date_end)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()  # the script will block here until the crawling is finished


@shared_task()
def parse_content_to_plaintext_task(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    logger.info('Adding content to each %s document.', website_name)
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"
    # Make sure solr index is updated
    core = 'documents'
    requests.get(os.environ['SOLR_URL'] +
                 '/' + core + '/update?commit=true')
    # select all records where content is empty and content_html is not
    q = "-content: [\"\" TO *] AND ( content_html: [* TO *] OR file_name: [* TO *] ) AND website:" + website_name
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    options = {'rows': rows_per_page, 'start': page_number,
               'cursorMark': cursor_mark, 'sort': 'id asc'}
    results = client.search(q, **options)
    items = []
    minio_client = Minio(os.environ['MINIO_STORAGE_ENDPOINT'], access_key=os.environ['MINIO_ACCESS_KEY'],
                         secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
    for result in results:
        # Parse content
        content_text = None
        if 'content_html' in result:
            output = parser.from_buffer(result['content_html'][0])
            content_text = output['content']
        elif 'file_name' in result:
            # If there is more than 1 pdf, we rely on score_documents to extract
            # the content of the pdf with the highest score
            if len(result['file_name']) == 1:
                try:
                    file_data = minio_client.get_object(
                        os.environ['MINIO_STORAGE_MEDIA_BUCKET_NAME'], result['file_name'][0])
                    output = BytesIO()
                    for d in file_data.stream(32*1024):
                        output.write(d)
                    content_text = parser.from_buffer(output.getvalue())
                    if 'content' in content_text:
                        content_text = content_text['content']
                except ResponseError as err:
                    print(err)

        # Store plaintext
        if content_text is None:
            # could not parse content
            logger.info(
                'No output for: %s, removing content', result['id'])
        else:
            logger.debug('Got content for: %s (%s)',
                         result['id'], len(content_text))

        # add to document model and save
        document = {"id": result['id'],
                    "content": {"set": content_text}}
        items.append(document)

        if len(items) == 1000:
            logger.info("Got 1000 items, posting to solr")
            client.add(items)
            requests.get(os.environ['SOLR_URL'] +
                         '/' + core + '/update?commit=true')
            items = []

    # Run solr commit: http://localhost:8983/solr/documents/update?commit=true
    client.add(items)
    requests.get(os.environ['SOLR_URL'] +
                 '/' + core + '/update?commit=true')


@shared_task
def sync_scrapy_to_solr_task(website_id):
    website = Website.objects.get(pk=website_id)
    logger.info("Scrapy to Solr WEBSITE: %s", str(website))
    # process files from minio
    minio_client = Minio(os.environ['MINIO_STORAGE_ENDPOINT'], access_key=os.environ['MINIO_ACCESS_KEY'],
                         secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
    bucket_name = website.name.lower()
    bucket_archive_name = bucket_name + "-archive"
    bucket_failed_name = bucket_name + "-failed"
    create_bucket(minio_client, bucket_name)
    create_bucket(minio_client, bucket_archive_name)
    create_bucket(minio_client, bucket_failed_name)
    core = "documents"
    try:
        objects = minio_client.list_objects(bucket_name)
        for obj in objects:
            logger.info("Working on %s", obj.object_name)
            file_data = minio_client.get_object(bucket_name, obj.object_name)
            url = os.environ['SOLR_URL'] + '/' + core + "/update/json/docs"
            output = BytesIO()
            for d in file_data.stream(32*1024):
                output.write(d)
            r = requests.post(url, output.getvalue())
            json_r = r.json()
            logger.info("SOLR RESPONSE: %s", json_r)
            if json_r['responseHeader']['status'] == 0:
                logger.info("ALL good, MOVE to '%s'", bucket_archive_name)
                copy_result = minio_client.copy_object(
                    bucket_archive_name, obj.object_name, bucket_name + "/" + obj.object_name)
            else:
                logger.info("NOT so good, MOVE to '%s'", bucket_failed_name)
                copy_result = minio_client.copy_object(
                    bucket_failed_name, obj.object_name, bucket_name + "/" + obj.object_name)

            minio_client.remove_object(bucket_name, obj.object_name)
        # Update solr index
        requests.get(os.environ['SOLR_URL'] + '/' +
                     core + '/update?commit=true')
    except ResponseError as err:
        raise


def create_bucket(client, name):
    try:
        client.make_bucket(name)
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass
