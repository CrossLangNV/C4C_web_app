import requests
import logging
import os
import json
from datetime import datetime
from urllib.request import urlopen, Request

from django.core.files.base import ContentFile
from django.db import transaction

from searchapp.models import Document, Attachment, Website

logger = logging.getLogger(__name__)


@transaction.atomic
def score_documents(django_documents):
    for django_doc in django_documents:
        url = os.environ['DOCUMENT_CLASSIFIER_URL'] + "/classify_doc"
        if(len(django_doc.summary)):
            data = {'document': django_doc.summary}
            response = requests.post(url, json=data)
            logger.info("Sending content: " + json.dumps(data))
            js = response.json()
            logger.info("Got response: " + json.dumps(js))
            django_doc.accepted_probability = js["accepted_probability"]
        else:
            django_doc.accepted_probability = 0
        django_doc.save()


@transaction.atomic
def sync_documents(website, solr_documents, django_documents):
    for solr_doc, django_doc_id in align_lists(solr_documents, django_documents):
        if solr_doc is None:
            break
        elif django_doc_id is None:
            solr_doc_date = solr_doc.get('date', [datetime.now()])[0]
            date_format = '%Y-%m-%dT%H:%M:%SZ'

            new_django_doc = Document.objects.create(
                id=solr_doc['id'],
                url=solr_doc['url'][0],
                celex=solr_doc.get('celex', [''])[0],
                eli=solr_doc.get('ELI', [''])[0],
                title_prefix=solr_doc.get('title_prefix', [''])[0],
                title=solr_doc.get('title', [''])[0],
                status=solr_doc.get('status', [''])[0],
                date=solr_doc_date,
                type=solr_doc.get('type', [''])[0],
                summary=''.join(x.strip()
                                for x in solr_doc.get('summary', [''])),
                content=''.join(x.strip()
                                for x in solr_doc.get('content', [''])),
                various=''.join(x.strip()
                                for x in solr_doc.get('various', [''])),
                website=website,
                pull=True
            )
        elif str(django_doc_id) == solr_doc['id']:
            # Document might have changed in solr. Update django_document
            update_document(Document.objects.get(pk=django_doc_id), solr_doc)
        else:
            logger.info('comparison failed')
            logger.info('django document id: ' + str(django_doc_id))
            logger.info('solr document id: ' + str(solr_doc['id']))


@transaction.atomic
def sync_attachments(document, solr_files, django_attachments):
    for solr_file, django_attachment_id in align_lists(solr_files, django_attachments):
        if solr_file is None:
            break
        elif django_attachment_id is None:
            new_django_attachment = Attachment.objects.create(
                id=solr_file['id'],
                url=solr_file['attr_url'][0],
                document=document,
                pull=True
            )
            save_file_from_url(new_django_attachment, solr_file)
        elif str(django_attachment_id) == solr_file['id']:
            update_attachment(Attachment.objects.get(
                pk=django_attachment_id), solr_file)
        else:
            logger.info('comparison failed')
            logger.info('django attachment id: ' + str(django_attachment_id))
            logger.info('solr file id: ' + str(solr_file['id']))


def update_document(django_doc, solr_doc):
    logger.info('update django document with id ' + solr_doc['id'])
    if 'date' in solr_doc:
        solr_doc_date = solr_doc['date'][0].split('T')[0]
        django_doc.date = datetime.strptime(solr_doc_date, '%Y-%m-%d')
    if 'url' in solr_doc:
        django_doc.url = solr_doc['url'][0]
    if 'title_prefix' in solr_doc:
        django_doc.title_prefix = solr_doc['title_prefix'][0]
    if 'title' in solr_doc:
        django_doc.title = solr_doc['title'][0]
    if 'type' in solr_doc:
        django_doc.type = solr_doc['type'][0]
    if 'summary' in solr_doc:
        django_doc.summary = ''.join(x.strip() for x in solr_doc['summary'])
    if 'website' in solr_doc:
        django_doc.website = Website.objects.get(
            name__iexact=solr_doc['website'][0])
    else:
        # FIXME: is this safe ?
        django_doc.acceptance_state = 'Unvalidated'
    django_doc.pull = False
    django_doc.save()


def update_attachment(django_attachment, solr_file):
    logger.info('update django attachment with id ' + solr_file['id'])
    django_attachment.url = solr_file['attr_url'][0]
    django_attachment.document = Document.objects.get(
        pk=solr_file['attr_document_id'][0])
    django_attachment.pull = False
    django_attachment.save()


# assumes lists are sorted, without duplicates and each element of a list contains an "id" property
# returns zip of lists
def align_lists(solr_items, django_items):
    django_items_ids = set()
    solr_items_ids = set()
    for django_item in django_items:
        django_items_ids.add(str(django_item.id))
    for solr_doc in solr_items:
        solr_items_ids.add(solr_doc['id'])

    new_django_items_ids = [
        x if x in django_items_ids else None for x in sorted(solr_items_ids)]
    logging.info(django_items_ids)
    logging.info(solr_items_ids)
    logging.info(new_django_items_ids)
    return zip(solr_items, new_django_items_ids)


def save_file_from_url(django_attachment, solr_file):
    headers = {
        'User-Agent': 'Mozilla/5.0(Windows NT 6.1) AppleWebKit/537.36(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'
    }
    req = Request(url=solr_file['attr_url'][0], headers=headers)
    response = urlopen(req)
    content = response.read()
    django_file = ContentFile(content)
    django_attachment.file.save(os.path.basename(
        solr_file['attr_resourcename'][0]), django_file)
