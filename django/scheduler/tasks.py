from __future__ import absolute_import, unicode_literals

import base64
import logging
import os
import shutil

from celery import shared_task
from jsonlines import jsonlines

from searchapp.models import Website
from searchapp.solr_call import solr_search, solr_search_document_id_sorted

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


@shared_task
def export_get_zip(task_id):
    file = open(workpath + '/export/' + task_id + '.zip', 'rb')
    bytes = file.read()
    base64_bytes = base64.b64encode(bytes)
    return base64_bytes.decode('ascii')


@shared_task
def export_delete_jsonl():
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


@shared_task
def export_delete_zip(task_id):
    # delete zip with given task id
    os.remove(workpath + '/export/' + task_id + '.zip')
