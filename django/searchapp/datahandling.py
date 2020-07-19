import base64
import json
import logging
import os
import random
import shutil
from datetime import datetime
from urllib.request import urlopen, Request

import requests
from django.core.files.base import ContentFile
from django.utils.timezone import make_aware
from jsonlines import jsonlines
from minio import Minio, ResponseError
from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists
from tika import parser

from searchapp.models import Document, Attachment, Website, AcceptanceState, AcceptanceStateValue
from searchapp.solr_call import solr_search_id

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))


def score_documents(website_name, django_documents, use_pdf_files):
    # if the classifier returns this value as either accepted or rejected
    # probability, it means something went wrong decoding the content
    error_classifier = -9999
    django_error_score = -1
    accepted_threshold = 0.5
    scores = []
    solr_documents = []
    for django_doc in django_documents:
        content = ''
        validated = False
        accepted_probability = error_classifier
        accepted_probability_index = 0
        # get content from solr
        solr_result = solr_search_id(core="documents", id=str(django_doc.id))
        if len(solr_result) == 1:
            solr_doc = solr_result[0]
            solr_documents.append(solr_doc)
            if use_pdf_files and solr_doc.get('pdf_docs'):
                # download each pdf file, parse with tika, use highest score
                pdf_urls = solr_doc['pdf_docs']
                classifier_responses = []
                for pdf_url in pdf_urls:
                    content = parse_pdf_from_url(pdf_url)
                    classifier_responses.append(classify(str(django_doc.id), content, 'pdf'))
                accepted_probability, accepted_probability_index = max(
                    [(r['accepted_probability'], i) for i, r in enumerate(classifier_responses)])
                if accepted_probability != error_classifier:
                    validated = True
                content = classifier_responses[accepted_probability_index]['content']
            elif solr_doc.get('content_html'):
                # classifier uses base64 content
                content = solr_doc['content_html'][0]
                classifier_response = classify(str(django_doc.id), content, 'html')
                accepted_probability = classifier_response["accepted_probability"]
                if accepted_probability != error_classifier:
                    validated = True
        else:
            solr_documents.append({})

        if validated:
            # for now acceptance_state_max_probability is the latest one
            django_doc.acceptance_state_max_probability = accepted_probability
            django_doc.pull = False
            django_doc.save()
            classifier_status = AcceptanceStateValue.ACCEPTED if accepted_probability > accepted_threshold else AcceptanceStateValue.REJECTED
            scores.append({'classifier_status': classifier_status, 'classifier_score': accepted_probability,
                           'content': content})
            AcceptanceState.objects.update_or_create(
                probability_model="auto classifier",
                document=django_doc,
                defaults={
                    'value': classifier_status,
                    'accepted_probability': accepted_probability,
                    'accepted_probability_index': accepted_probability_index
                }
            )
        else:
            # couldn't classify
            django_doc.acceptance_state_max_probability = django_error_score
            django_doc.pull = False
            django_doc.save()
            scores.append({'classifier_status': AcceptanceStateValue.UNVALIDATED, 'classifier_score': django_error_score,
                           'content': content})
            AcceptanceState.objects.update_or_create(
                probability_model="auto classifier",
                document=django_doc,
                defaults={
                    'value': AcceptanceStateValue.UNVALIDATED,
                    'accepted_probability': django_error_score,
                    'accepted_probability_index': accepted_probability_index
                }
            )
    score_export(website_name, solr_documents, scores)


def score_export(website_name, documents, scores):
    for document, score in zip(documents, scores):
        if document:
            with jsonlines.open(workpath + '/score/jsonl/' + website_name + '/doc_' + document['id'] + '.jsonl',
                                mode='w') as f:
                f.write(document)
                f.write(score)

    # create zip file for all .jsonl files
    zip_destination = workpath + '/score'
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
        'export', '.zip', zip_destination + '.zip')


def parse_pdf_from_url(url):
    user_agent_list = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    ]
    user_agent = random.choice(user_agent_list)
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.info('PARSE PDF WITH TIKA...')
        pdf_text = parser.from_buffer(response.content)
        if pdf_text['content']:
            return pdf_text['content']
    logging.error(response.text)
    return ''


def classify(django_doc_id, content, content_type):
    classifier_url = os.environ['DOCUMENT_CLASSIFIER_URL'] + "/classify_doc"
    error_classifier = -9999
    max_content_size_bytes = 50 * 1024 * 1024
    content_bytes = bytes(content, 'utf-8')
    # don't classify if content > max_content_size_bytes
    if len(content_bytes) <= max_content_size_bytes:
        content_html_b64 = base64.b64encode(
            content_bytes).decode('utf-8')
        data = {'content': content_html_b64,
                'content_type': content_type}
        logger.info("Sending content for doc id: " + django_doc_id)
        response = requests.post(classifier_url, json=data)
        js = response.json()
        js['content'] = content
        logger.info("Got classifier response: " + json.dumps(js))
        if 'accepted_probability' not in js:
            logger.error('Something went wrong, return ERROR classifier score')
            js = {'accepted_probability': error_classifier, 'content': content}
        return js
    logger.error('Something went wrong, return ERROR classifier score')
    return {'accepted_probability': error_classifier, 'content': content}


def sync_documents(website, solr_documents, django_documents):
    for solr_doc, django_doc_id in align_lists(solr_documents, django_documents):
        if solr_doc is None:
            break
        elif django_doc_id is None:
            solr_doc_date = solr_doc.get('date', [datetime.now()])[0]
            new_django_doc = Document.objects.create(
                id=solr_doc['id'],
                url=solr_doc['url'][0],
                celex=solr_doc.get('celex', [''])[0][:20],
                eli=solr_doc.get('ELI', [''])[0],
                title_prefix=solr_doc.get('title_prefix', [''])[0],
                title=solr_doc.get('title', [''])[0][:1000],
                status=solr_doc.get('status', [''])[0][:100],
                date=solr_doc_date,
                type=solr_doc.get('type', [''])[0],
                summary=''.join(x.strip()
                                for x in solr_doc.get('summary', [''])),
                various=''.join(x.strip()
                                for x in solr_doc.get('various', [''])),
                website=website,
                consolidated_versions=','.join(x.strip()
                                               for x in solr_doc.get('consolidated_versions', [''])),
                pull=True
            )
        elif str(django_doc_id) == solr_doc['id']:
            # Document might have changed in solr. Update django_document
            update_document(Document.objects.get(pk=django_doc_id), solr_doc)
        else:
            logger.info('comparison failed')
            logger.info('django document id: ' + str(django_doc_id))
            logger.info('solr document id: ' + str(solr_doc['id']))


def sync_attachments(document, solr_files, django_attachments):
    for solr_file, django_attachment_id in align_lists(solr_files, django_attachments):
        logger.info("SYNCATT: working on " + str(django_attachment_id))
        if solr_file is None:
            break
        elif django_attachment_id is None:
            new_django_attachment = Attachment.objects.create(
                id=solr_file['id'],
                url=solr_file['attr_url'][0],
                document=document,
                extracted=True
            )
        # save_file_from_url(new_django_attachment, solr_file)
        elif str(django_attachment_id) == solr_file['id']:
            update_attachment(Attachment.objects.get(
                pk=django_attachment_id), solr_file)
        else:
            logger.info('comparison failed')
            logger.info('django attachment id: ' + str(django_attachment_id))
            logger.info('solr file id: ' + str(solr_file['id']))


def update_document(django_doc, solr_doc):
    logger.info('update django document with id ' + solr_doc['id'])
    if 'url' in solr_doc:
        django_doc.url = solr_doc['url'][0]
    if 'celex' in solr_doc:
        django_doc.celex = solr_doc['celex'][0][:20]
    if 'eli' in solr_doc:
        django_doc.eli = solr_doc['eli'][0]
    if 'title_prefix' in solr_doc:
        django_doc.title_prefix = solr_doc['title_prefix'][0]
    if 'title' in solr_doc:
        django_doc.title = solr_doc['title'][0][:1000]
    if 'status' in solr_doc:
        django_doc.status = solr_doc['status'][0][:100]
    if 'date' in solr_doc:
        solr_doc_date = solr_doc['date'][0].split('T')[0]
        django_doc.date = make_aware(
            datetime.strptime(solr_doc_date, '%Y-%m-%d'))
    if 'type' in solr_doc:
        django_doc.type = solr_doc['type'][0]
    if 'summary' in solr_doc:
        django_doc.summary = ''.join(x.strip() for x in solr_doc['summary'])
    if 'various' in solr_doc:
        django_doc.various = ''.join(x.strip() for x in solr_doc['various'])
    if 'consolidated_versions' in solr_doc:
        django_doc.consolidated_versions = ','.join(
            x.strip() for x in solr_doc['consolidated_versions'])
    if 'website' in solr_doc:
        django_doc.website = Website.objects.get(
            name__iexact=solr_doc['website'][0])
    # Don't update solr when syncing from solr to django
    django_doc.pull = True
    django_doc.save()


def update_attachment(django_attachment, solr_file):
    logger.info('update django attachment with id ' + solr_file['id'])
    django_attachment.url = solr_file['attr_url'][0]
    django_attachment.document = Document.objects.get(
        pk=solr_file['attr_document_id'][0])
    django_attachment.extracted = False
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
