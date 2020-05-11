import logging
import os

from background_task import background
from django.utils import timezone
from scrapyd_api import ScrapydAPI

from .datahandling import score_documents, sync_documents, sync_attachments
from .models import Website, Document, Attachment
from .solr_call import solr_search_website_sorted, solr_search_document_id_sorted

logger = logging.getLogger(__name__)


@background(schedule=timezone.now())
def score_documents_task(website_id):
    logger.info("Scoring documents with WEBSITE: " + str(website_id))
    # lookup documents for website and score them
    website = Website.objects.get(pk=website_id)
    django_documents = Document.objects.filter(website=website).order_by('id')
    score_documents(django_documents)


@background(schedule=timezone.now())
def sync_documents_task(website_id):
    logger.info("Syncing documents with WEBSITE: " + str(website_id))
    # lookup documents for website and sync them
    website = Website.objects.get(pk=website_id)
    django_documents = Document.objects.filter(website=website).order_by('id')
    # query Solr for available documents and sync with Django
    solr_documents = solr_search_website_sorted(
        core='documents', website=website.name.lower())
    sync_documents(website, solr_documents, django_documents)


@background(schedule=timezone.now())
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


@background(schedule=timezone.now())
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
