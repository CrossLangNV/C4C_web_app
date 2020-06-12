from __future__ import absolute_import, unicode_literals

import logging
import os
import shutil

import requests
from celery import shared_task
from django.db.models.functions import Length
from jsonlines import jsonlines
from minio import Minio, ResponseError
from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists
from scrapyd_api import ScrapydAPI
from tika import parser

from searchapp.datahandling import score_documents, sync_documents, sync_attachments
from searchapp.models import Website, Document, Attachment
from searchapp.solr_call import solr_search, solr_search_document_id_sorted, solr_search_website_sorted

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))


@shared_task
def export_documents(website_ids=None):
    websites = Website.objects.all()
    if website_ids:
        websites = Website.objects.filter(pk__in=website_ids)
    for website in websites:
        if not os.path.exists(workpath + '/export/jsonl/' + website.name):
            os.makedirs(workpath + '/export/jsonl/' + website.name)
        documents = solr_search(
            core='documents', term='website:' + website.name)
        for document in documents:
            files = solr_search_document_id_sorted(
                core='files', document_id=document['id'])
            with jsonlines.open(workpath + '/export/jsonl/' + website.name + '/doc_' + document['id'] + '.jsonl',
                                mode='w') as f:
                f.write(document)
                for file in files:
                    f.write(file)

    # create zip file for all .jsonl files
    zip_destination = workpath + '/export/' + export_documents.request.id
    shutil.make_archive(zip_destination, 'zip', workpath + '/export/jsonl')

    # upload zip to minio
    minio_client = Minio('minio:9000', access_key=os.environ['MINIO_ACCESS_KEY'],
                         secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
    try:
        minio_client.make_bucket('export')
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass
    except ResponseError as err:
        raise
    minio_client.fput_object('export', export_documents.request.id + '.zip', zip_destination + '.zip')


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
    logger.info("Scoring documents with WEBSITE: " + str(website_id))
    # lookup documents for website and score them
    website = Website.objects.get(pk=website_id)
    django_documents = Document.objects.filter(website=website).order_by('id')
    score_documents(django_documents)


@shared_task
def sync_documents_task(website_id):
    logger.info("Syncing documents with WEBSITE: " + str(website_id))
    # lookup documents for website and sync them
    website = Website.objects.get(pk=website_id)
    django_documents = Document.objects.filter(website=website).order_by('id')
    # query Solr for available documents and sync with Django
    solr_documents = solr_search_website_sorted(
        core='documents', website=website.name.lower())
    sync_documents(website, solr_documents, django_documents)


@shared_task
def sync_attachments_task(website_id):
    logger.info("Synching attachments with WEBSITE: " + str(website_id))
    # lookup documents for website and sync them
    website = Website.objects.get(pk=website_id)
    for document in Document.objects.filter(website=website).order_by('id'):
        # query Solr for attachments
        solr_files = solr_search_document_id_sorted(
            core='files', document_id=str(document.id))
        attachments = Attachment.objects.filter(
            document=document).order_by('id')
        sync_attachments(document, solr_files, attachments)


@shared_task
def scrape_website_task(website_id):
    logger.info("Scraping with WEBSITE: " + str(website_id))
    # lookup website and start scraping
    website = Website.objects.get(pk=website_id)
    # custom settings for spider
    settings = {
        'task_id': '1'
    }
    spiders = [{"id": "bis"}, {"id": "eiopa"}, {"id": "esma"}, {
        "id": "eurlex", "type": "directives"}, {"id": "eurlex", "type": "decisions"},
               {"id": "eurlex", "type": "regulations"}, {"id": "fsb"}, {"id": "srb"},
               {"id": "eba", "type": "guidelines"}, {
                   "id": "eba", "type": "recommendations"},
               ]
    for spider in spiders:
        if spider['id'].lower() == website.name.lower():
            scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])
            scrapyd_project = 'default'
            if 'type' not in spider:
                spider['type'] = ''
            # schedule scraping task
            scrapyd_task_id = scrapyd.schedule(
                'default', spider['id'], settings=settings, spider_type=spider['type'])


@shared_task(default_retry_delay=1 * 60, max_retries=10)
def add_content_eurlex():
    cellar_api_endpoint = 'http://publications.europa.eu/resource/celex/'
    pdf_endpoint = 'https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:'

    logger.info('Adding content to each eurlex document.')
    website_eurlex = Website.objects.get(name__iexact='eurlex')
    # filter on content_html length < 1
    documents = Document.objects.annotate(text_len=Length('content_html')) \
        .filter(website=website_eurlex, text_len__lt=1)

    global headers
    global response
    global content_html

    for document in documents:
        logger.info('Requesting xhtml content for celex id: %s', document.celex)
        headers = {'Accept': 'application/xhtml+xml', 'Accept-Language': 'eng'}
        response = requests.get(cellar_api_endpoint + document.celex, headers=headers)
        content_html = response.text
        if response.status_code != 200:
            logger.info('FALLBACK: Requesting html content for celex id: %s', document.celex)
            headers = {'Accept': 'text/html', 'Accept-Language': 'eng'}
            response = requests.get(cellar_api_endpoint + document.celex, headers=headers)
            content_html = response.text
            if response.status_code != 200:
                logger.info('FALLBACK: Requesting pdf content for celex id: %s', document.celex)
                response = requests.get(pdf_endpoint + document.celex)
                if response.status_code == 200:
                    logger.info('PARSE PDF WITH TIKA...')
                    pdf_text = parser.from_buffer(response.content, xmlContent=True)
                    if pdf_text['content'] is None:
                        logger.error('Unable to parse pdf.')
                        content_html = None
                    else:
                        content_html = pdf_text['content']
                else:
                    content_html = None

        if content_html:
            content = parser.from_buffer(content_html)['content']
            # add to document model and save
            logger.info('Got content_html for: %s', document.celex)
            document.content_html = content_html
            if content:
                logger.info('Parsed content from content_html for: %s', document.celex)
                document.content = content
            document.pull = False
            document.save()
            logger.info('Saved content for: %s', document.celex)
