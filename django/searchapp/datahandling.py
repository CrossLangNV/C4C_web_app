from searchapp.solr_call import solr_search_id
from searchapp.models import Document, Attachment, Website, AcceptanceState, AcceptanceStateValue
from tika import parser
from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists
from minio import Minio, ResponseError
from jsonlines import jsonlines
import base64
import json
import logging
import os
import random
import shutil
import pysolr
from datetime import datetime
from urllib.request import urlopen, Request

import requests
from django.core.files.base import ContentFile
from django.utils.timezone import make_aware
from django.db.models import Q, Count


logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))


def score_documents(website_name, solr_documents, use_pdf_files):
    # if the classifier returns this value as either accepted or rejected
    # probability, it means something went wrong decoding the content
    CLASSIFIER_ERROR_SCORE = -9999
    DJANGO_ERROR_SCORE = -1
    ACCEPTED_THRESHOLD = 0.5
    scores = []
    django_docs = []
    score_updates = []
    content_updates = []
    # Tweak pysolr logger output
    LOG = logging.getLogger("pysolr")
    LOG.setLevel(logging.WARNING)
    # loop documents
    for solr_doc in solr_documents:
        content = ''
        accepted_probability = CLASSIFIER_ERROR_SCORE
        accepted_probability_index = 0
        if use_pdf_files and solr_doc.get('pdf_docs'):
            # download each pdf file, parse with tika, use highest score
            pdf_urls = solr_doc['pdf_docs']
            classifier_responses = []
            if solr_doc.get('content') and len(solr_doc.get('content')) > 0:
                content = solr_doc['content'][0]
                classifier_response = classify(
                    str(solr_doc["id"]), content, 'pdf')
                accepted_probability = classifier_response["accepted_probability"]
            else:
                for pdf_url in pdf_urls:
                    logger.info("Going to parse PDF with url: %s", pdf_url)
                    content = parse_pdf_from_url(pdf_url)
                    classifier_responses.append(
                        classify(str(solr_doc["id"]), content, 'pdf'))
                    # Take highest scoring
                content = classifier_responses[accepted_probability_index]['content']
                content_updates.append({"id": solr_doc["id"],
                                        "content": {"set": content}})
                accepted_probability, accepted_probability_index = max(
                    [(r['accepted_probability'], i) for i, r in enumerate(classifier_responses)])
        elif solr_doc.get('content_html'):
            # classifier uses base64 content
            content = solr_doc['content_html'][0]
            classifier_response = classify(
                str(solr_doc["id"]), content, 'html')
            accepted_probability = classifier_response["accepted_probability"]

        # Check acceptance
        if accepted_probability != CLASSIFIER_ERROR_SCORE:
            # Validated
            classifier_status = AcceptanceStateValue.ACCEPTED if accepted_probability > ACCEPTED_THRESHOLD else AcceptanceStateValue.REJECTED
        else:
            # couldn't classify
            accepted_probability = DJANGO_ERROR_SCORE
            classifier_status = AcceptanceStateValue.UNVALIDATED

        # Storage
        django_doc = Document.objects.get(pk=solr_doc["id"])
        django_doc.acceptance_state_max_probability = accepted_probability
        django_doc.save()
        score_updates.append({"id": solr_doc["id"],
                              "accepted_probability": {"set": accepted_probability},
                              "acceptance_state": {"set": classifier_status}})
        # Storage for export (disabled ATM)
        django_docs.append(django_doc)
        scores.append({'classifier_status': classifier_status, 'classifier_score': accepted_probability,
                       'content': content})
        # Store AcceptanceState
        AcceptanceState.objects.update_or_create(
            probability_model="auto classifier",
            document=django_doc,
            defaults={
                'value': classifier_status,
                'accepted_probability': accepted_probability,
                'accepted_probability_index': accepted_probability_index
            }
        )

    # Store scores (and content) in solr
    logger.info("Posting %d scores to SOLR", len(score_updates))
    core = 'documents'
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    client.add(score_updates)
    client.add(content_updates)

    # Add unvalidated state for documents without AcceptanceState
    # This can happen when documents didn't have content of couldn't calculate a score
    logger.info("Handling documents without AcceptanceState...")
    website = Website.objects.get(name=website_name)
    docs = Document.objects.filter(Q(website=website) & Q(
        acceptance_state_max_probability__isnull=True))
    for doc in docs:
        logger.info("CREATE: %s", doc.id)
        AcceptanceState.objects.update_or_create(
            probability_model="auto classifier",
            document=doc,
            defaults={
                'value': AcceptanceStateValue.UNVALIDATED,
                'accepted_probability': DJANGO_ERROR_SCORE,
                'accepted_probability_index': 0
            }
        )
        doc.acceptance_state_max_probability = DJANGO_ERROR_SCORE
        doc.save()

    # Update solr index
    logger.info("Committing SOLR index...")
    core = 'documents'
    requests.get(os.environ['SOLR_URL'] +
                 '/' + core + '/update?commit=true')
    # score_export(website_name, solr_documents, scores)


def score_export(website_name, documents, scores):
    if not os.path.exists(workpath + '/score/jsonl/' + website_name):
        os.makedirs(workpath + '/score/jsonl/' + website_name)
    for document, score in zip(documents, scores):
        if document:
            with jsonlines.open(workpath + '/score/jsonl/' + website_name + '/doc_' + document['id'] + '.jsonl',
                                mode='w') as f:
                f.write(document)
                f.write(score)

    # create zip file for all .jsonl files
    zip_destination = workpath + '/score'
    shutil.make_archive(zip_destination, 'zip', workpath + '/score/jsonl')

    # upload zip to minio
    minio_client = Minio(os.environ['MINIO_STORAGE_ENDPOINT'], access_key=os.environ['MINIO_ACCESS_KEY'],
                         secret_key=os.environ['MINIO_SECRET_KEY'], secure=False)
    try:
        minio_client.make_bucket('score')
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass
    except ResponseError as err:
        raise
    minio_client.fput_object(
        'score', '.zip', zip_destination + '.zip')


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
    CLASSIFIER_ERROR_SCORE = -9999
    max_content_size_bytes = 50 * 1024 * 1024
    content_bytes = bytes(content, 'utf-8')
    # don't classify if content > max_content_size_bytes
    if len(content_bytes) <= max_content_size_bytes:
        content_html_b64 = base64.b64encode(
            content_bytes).decode('utf-8')
        data = {'content': content_html_b64,
                'content_type': content_type}
        logger.debug("Sending content for doc id: " + django_doc_id)
        response = requests.post(classifier_url, json=data)
        js = response.json()
        js['content'] = content
        logger.debug("Got classifier response: " + json.dumps(js))
        if 'accepted_probability' not in js:
            logger.error('Something went wrong, return ERROR classifier score')
            js = {'accepted_probability': CLASSIFIER_ERROR_SCORE, 'content': content}
        return js
    logger.error('Something went wrong, return RROR classifier score')
    return {'accepted_probability': CLASSIFIER_ERROR_SCORE, 'content': content}


def sync_documents(website, solr_documents, django_documents):
    for solr_doc, django_doc_id in align_lists(solr_documents, django_documents):
        if solr_doc is None:
            break
        elif django_doc_id is None:
            solr_doc_date = solr_doc.get('date', [datetime.now()])[0]
            solr_doc_date_last_update = solr_doc.get(
                'date_last_update', datetime.now())
            new_django_doc = Document.objects.create(
                id=solr_doc['id'],
                url=solr_doc['url'][0],
                celex=solr_doc.get('celex', [''])[0][:20],
                eli=solr_doc.get('ELI', [''])[0],
                title_prefix=solr_doc.get('title_prefix', [''])[0],
                title=solr_doc.get('title', [''])[0][:1000],
                status=solr_doc.get('status', [''])[0][:100],
                date=solr_doc_date,
                date_last_update=solr_doc_date_last_update,
                file_url=solr_doc.get('file_url', [None])[0],
                type=solr_doc.get('type', [''])[0],
                summary=''.join(x.strip()
                                for x in solr_doc.get('summary', [''])),
                various=''.join(x.strip()
                                for x in solr_doc.get('various', [''])),
                website=website,
                consolidated_versions=','.join(x.strip()
                                               for x in solr_doc.get('consolidated_versions', [''])),
            )
        elif str(django_doc_id) == solr_doc['id']:
            # Document might have changed in solr. Update django_document
            update_document(Document.objects.get(pk=django_doc_id), solr_doc)
        else:
            logger.info('comparison failed')
            logger.info('django document id: ' + str(django_doc_id))
            logger.info('solr document id: ' + str(solr_doc['id']))


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
    if 'date_last_update' in solr_doc:
        solr_doc_date = solr_doc['date_last_update']
        django_doc.date_last_update = make_aware(datetime.strptime(
            solr_doc_date, '%Y-%m-%dT%H:%M:%SZ'))
    if 'file_url' in solr_doc:
        django_doc.file_url = solr_doc['file_url'][0]
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
