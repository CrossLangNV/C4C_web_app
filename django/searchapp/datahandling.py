import json
import os
from datetime import datetime
from itertools import zip_longest
from urllib.request import urlopen, Request

from django.core.files.base import ContentFile

from searchapp.models import Document, Attachment, Website

import logging


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
                date=datetime.strptime(solr_doc_date, date_format),
                type=solr_doc.get('type', [''])[0],
                summary=''.join(x.strip() for x in solr_doc.get('summary', [''])),
                content=''.join(x.strip() for x in solr_doc.get('content', [''])),
                various=''.join(x.strip() for x in solr_doc.get('various', [''])),
                website=website,
                pull=True
            )
        elif str(django_doc_id) == solr_doc['id']:
            update_document(Document.objects.get(pk=django_doc_id), solr_doc)
        else:
            print('comparison failed')
            print('django document id: ' + str(django_doc_id))
            print('solr document id: ' + str(solr_doc['id']))


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
            update_attachment(Attachment.objects.get(pk=django_attachment_id), solr_file)
        else:
            print('comparison failed')
            print('django attachment id: ' + str(django_attachment_id))
            print('solr file id: ' + str(solr_file['id']))


def update_document(django_doc, solr_doc):
    print('update django document with id ' + solr_doc['id'])
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
        django_doc.website = Website.objects.get(name__iexact=solr_doc['website'][0])
    else:
        django_doc.acceptance_state = 'Unvalidated'
    django_doc.pull = False
    django_doc.save()


def update_attachment(django_attachment, solr_file):
    print('update django attachment with id ' + solr_file['id'])
    django_attachment.url = solr_file['attr_url'][0]
    django_attachment.document = Document.objects.get(pk=solr_file['attr_document_id'][0])
    django_attachment.pull = False
    django_attachment.save()


# assumes lists are sorted, without duplicates and each element of a list contains an "id" property
# returns zip of lists
def align_lists(solr_docs, django_docs):
    django_docs_ids = set()
    solr_docs_ids = set()
    for django_doc in django_docs:
        django_docs_ids.add(str(django_doc.id))
    for solr_doc in solr_docs:
        solr_docs_ids.add(solr_doc['id'])

    new_django_docs_ids = [x if x in django_docs_ids else None for x in sorted(solr_docs_ids)]
    logging.info(django_docs_ids)
    logging.info(solr_docs_ids)
    logging.info(new_django_docs_ids)
    return zip(solr_docs, new_django_docs_ids)


def save_file_from_url(django_attachment, solr_file):
    headers = {
        'User-Agent': 'Mozilla/5.0(Windows NT 6.1) AppleWebKit/537.36(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'
    }
    req = Request(url=solr_file['attr_url'][0], headers=headers)
    response = urlopen(req)
    content = response.read()
    django_file = ContentFile(content)
    django_attachment.file.save(os.path.basename(solr_file['attr_resourcename'][0]), django_file)
