import base64
import json
import logging
import os

import pysolr
import requests
from django.db.models import Q

from searchapp.models import Document, Website, AcceptanceState, AcceptanceStateValue

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))


def score_documents(website_name, solr_documents):
    # if the classifier returns this value as either accepted or rejected
    # probability, it means something went wrong decoding the content
    CLASSIFIER_ERROR_SCORE = -9999
    DJANGO_ERROR_SCORE = -1
    ACCEPTED_THRESHOLD = 0.5
    score_updates = []
    content_updates = []
    core = 'documents'
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    # loop documents
    for solr_doc in solr_documents:
        content = ''
        accepted_probability = CLASSIFIER_ERROR_SCORE
        accepted_probability_index = 0

        if solr_doc.get('content'):
            # classifier uses base64 content
            content = solr_doc['content'][0]
            classifier_response = classify(
                str(solr_doc["id"]), content, solr_doc["language"])
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
        if len(score_updates) == 1000:
            logger.info("Posting %d scores to SOLR", len(score_updates))
            client.add(score_updates)
            score_updates = []
            requests.get(os.environ['SOLR_URL'] +
                         '/' + core + '/update?commit=true')

        if len(content_updates) == 10:
            logger.info("Posting %d content to SOLR", len(content_updates))
            client.add(content_updates)
            content_updates = []
            requests.get(os.environ['SOLR_URL'] +
                         '/' + core + '/update?commit=true')

    # Add unvalidated state for documents without AcceptanceState
    # This can happen when documents didn't have content or couldn't calculate a score
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

    # Flush last updates
    client.add(score_updates)
    client.add(content_updates)
    # Update solr index
    logger.info("Committing SOLR index...")
    core = 'documents'
    requests.get(os.environ['SOLR_URL'] + '/' + core + '/update?commit=true')


def classify(django_doc_id, content, language):
    classifier_url = os.environ['DOCUMENT_CLASSIFIER_URL'] + "/classify_doc"
    CLASSIFIER_ERROR_SCORE = -9999
    max_content_size_bytes = 50 * 1024 * 1024
    content_bytes = bytes(content, 'utf-8')
    # don't classify if content > max_content_size_bytes
    if len(content_bytes) <= max_content_size_bytes:
        content_html_b64 = base64.b64encode(
            content_bytes).decode('utf-8')
        data = {'content': content_html_b64,
                'language': language}
        logger.debug("Sending content for doc id: " + django_doc_id)
        response = requests.post(classifier_url, json=data)
        js = response.json()
        js['content'] = content
        logger.debug("Got classifier response: " + json.dumps(js))
        if 'accepted_probability' not in js:
            logger.error('Something went wrong, return ERROR classifier score')
            js = {'accepted_probability': CLASSIFIER_ERROR_SCORE, 'content': content}
        return js
    logger.error('Something went wrong, return ERROR classifier score')
    return {'accepted_probability': CLASSIFIER_ERROR_SCORE, 'content': content}
