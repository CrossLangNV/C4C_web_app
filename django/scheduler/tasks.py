from __future__ import absolute_import, unicode_literals

import base64
import json
import logging
import os
import shutil
import time
import urllib
from datetime import datetime, timedelta
from io import BytesIO

import cassis
import pysolr
import requests
from cassis import Cas, load_cas_from_xmi
from cassis.typesystem import load_typesystem
from celery import shared_task, chain
from django.core.exceptions import ValidationError
from django.db.models.functions import Length
from jsonlines import jsonlines
from langdetect import detect_langs
from langdetect.lang_detect_exception import LangDetectException
from minio import Minio, ResponseError
from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from tika import parser
from twisted.internet import reactor

from glossary.models import Concept, ConceptOccurs, ConceptDefined
from searchapp.datahandling import score_documents
from searchapp.models import Website, Document, AcceptanceState, Tag, AcceptanceStateValue
from searchapp.solr_call import solr_search_website_sorted, solr_search_website_with_content

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))

sofa_id_html2text = "html2textView"
sofa_id_text2html = "text2htmlView"
UIMA_URL = {"BASE": os.environ['GLOSSARY_UIMA_URL'],  # http://uima:8008
            "HTML2TEXT": "/html2text",
            "TEXT2HTML": "/text2html",
            "TYPESYSTEM": "/html2text/typesystem",
            }
# TODO Theres already a solr defined
SOLR_URL = os.environ['SOLR_URL']
# Don't remove the '/' at the end here
TERM_EXTRACT_URL = os.environ['GLOSSARY_TERM_EXTRACT_URL']
DEFINITIONS_EXTRACT_URL = os.environ['GLOSSARY_DEFINITIONS_EXTRACT_URL']
PARAGRAPH_DETECT_URL = os.environ['GLOSSARY_PARAGRAPH_DETECT_URL']
RO_EXTRACT_URL = os.environ['RO_EXTRACT_URL']
SENTENCE_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
TFIDF_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.frequency.tfidf.type.Tfidf"
LEMMA_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"
PARAGRAPH_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph"
VALUE_BETWEEN_TAG_TYPE_CLASS = "com.crosslang.uimahtmltotext.uima.type.ValueBetweenTagType"


@shared_task()
def delete_deprecated_acceptance_states():
    acceptance_states = AcceptanceState.objects.all().order_by("document").distinct(
        "document_id").annotate(text_len=Length('document__title')).filter(text_len__gt=1).values()
    documents = Document.objects.all().annotate(text_len=Length('title')).filter(
        text_len__gt=1).values()

    documents = [str(doc['id']) for doc in documents]
    acceptances = [str(acc['document_id']) for acc in acceptance_states]

    diff = list(set(acceptances) - set(documents))
    count = AcceptanceState.objects.all().filter(document_id__in=diff).delete()

    logger.info("Deleted %s deprecated acceptance states", count)


@shared_task
def reset_pre_analyzed_fields(website_id):
    website = Website.objects.get(pk=website_id)
    logger.info("Resetting all PreAnalyzed fields for WEBSITE: %s", website.name)

    website_name = website.name.lower()
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"
    # Make sure solr index is updated
    core = 'documents'
    requests.get(os.environ['SOLR_URL'] +
                 '/' + core + '/update?commit=true')
    # select all records where content is empty and content_html is not
    q = "( concept_occurs: [* TO *] OR concept_defined: [* TO *] ) AND website:" + website_name
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    options = {'rows': rows_per_page, 'start': page_number,
               'cursorMark': cursor_mark, 'sort': 'id asc'}
    results = client.search(q, **options)
    items = []

    for result in results:
        # add to document model and save
        document = {"id": result['id'],
                    "concept_occurs": {"set": "null"},
                    "concept_defined": {"set": "null"}
                    }
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
def full_service_task(website_id, **kwargs):
    website = Website.objects.get(pk=website_id)
    logger.info("Full service for WEBSITE: %s", website.name)
    # the following subtasks are linked together in order:
    # sync_scrapy_to_solr -> parse_content -> sync (solr to django) -> score
    # a task only starts after the previous finished, immutable signatures (si)
    # are used since a task doesn't need the result of the previous task: see
    # https://docs.celeryproject.org/en/stable/userguide/canvas.html
    chain(
        sync_scrapy_to_solr_task.si(website_id),
        parse_content_to_plaintext_task.si(
            website_id, date=kwargs.get('date', None)),
        sync_documents_task.si(website_id, date=kwargs.get('date', None)),
        score_documents_task.si(website_id, date=kwargs.get('date', None)),
        check_documents_unvalidated_task.si(website_id),
        extract_terms.si(website_id),
    )()


@shared_task
def export_documents(website_ids=None):
    websites = Website.objects.all()
    logger.info("Export for websites: %s", website_ids)
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
        workdir = workpath + '/export/' + \
                  export_documents.request.id + '/' + website.name.lower()
        os.makedirs(workdir)
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
            with jsonlines.open(workdir + '/doc_' + document['id'] + '.jsonl',
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
    shutil.make_archive(zip_destination, 'zip', workpath +
                        '/export/' + export_documents.request.id)

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

    shutil.rmtree(workpath + '/export/' + export_documents.request.id)
    os.remove(zip_destination + '.zip')
    logging.info("Removed: %s", zip_destination + '.zip')


def post_pre_analyzed_to_solr(data):
    params = json.dumps(data).encode('utf8')
    req = urllib.request.Request(os.environ['SOLR_URL'] + "/documents/update", data=params,
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    logger.info(response.read().decode('utf8'))


@shared_task
def get_stats_for_html_size(website_id):
    core = 'documents'
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"

    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    q = "website:" + website_name + " AND content_html:* AND acceptance_state:accepted"

    # Load all documents from Solr
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    options = {'rows': rows_per_page, 'start': page_number,
               'cursorMark': cursor_mark, 'sort': 'id asc', 'fl': 'content_html,id'}
    documents = client.search(q, **options)

    size_1 = 0
    size_2 = 0
    for document in documents:
        if document['content_html'] is not None:
            if len(document['content_html'][0]) > 500000:
                size_1 = size_1 + 1
                logger.info("500K document id: %s", document['id'])
            elif len(document['content_html'][0]) > 1000000:
                size_2 = size_2 + 1
                logger.info("1M document id: %s", document['id'])

    logger.info("[Document stats]: Documents over 500k lines: %s", size_1)
    logger.info("[Document stats]: Documents over 1M lines: %s", size_2)


def get_html2text_cas(content_html):
    content_html_text = {
        "text": content_html
    }
    start = time.time()
    r = requests.post(
        UIMA_URL["BASE"] + UIMA_URL["HTML2TEXT"], json=content_html_text)

    logger.info('Sent request to %s. Status code: %s', UIMA_URL["BASE"] + UIMA_URL["HTML2TEXT"],
                r.status_code)
    end = time.time()
    logger.info(
        "UIMA Html2Text took %s seconds to succeed.", end - start)
    return r


def create_cas(sofa):
    with open("typesystem_tmp.xml", 'rb') as f:
        ts = load_typesystem(f)

    cas = Cas(typesystem=ts)
    cas.sofa_string = sofa
    return cas


def get_cas_from_pdf(content):
    logger.info("its a pdf")
    # Logic for documents without HTML, that have a "content" field which is a PDF to HTML done by Tika
    # Create a new cas here
    tika_cas = create_cas(content)

    encoded_cas = base64.b64encode(bytes(tika_cas.to_xmi(), 'utf-8')).decode()

    # Then send this cas to NLP Paragraph detection
    input_for_paragraph_detection = {
        "cas_content": encoded_cas,
        "content_type": "pdf",
    }
    return requests.post(PARAGRAPH_DETECT_URL,
                      json=input_for_paragraph_detection)


def fetch_typesystem():
    typesystem_req = requests.get(
        UIMA_URL["BASE"] + UIMA_URL["TYPESYSTEM"])
    typesystem_file = open("/tmp/typesystem.xml", "w")
    typesystem_file.write(typesystem_req.content.decode("utf-8"))
    with open('/tmp/typesystem.xml', 'rb') as f:
      return load_typesystem(f)


def get_cas_from_paragraph_detection(content_encoded):
    input_for_paragraph_detection = {
        "cas_content": content_encoded,
        "content_type": "html",
    }

    paragraph_request = requests.post(PARAGRAPH_DETECT_URL,
                                      json=input_for_paragraph_detection)
    logger.info("Sent request to Paragraph Detection. Status code: %s",
                paragraph_request.status_code)

    return paragraph_request


def get_reporting_obligations(input_cas_encoded):
    input_for_reporting_obligations = {
        "cas_content": input_cas_encoded,
        "content_type": "html",
    }

    ro_request = requests.post(RO_EXTRACT_URL,
                               json=input_for_reporting_obligations)
    logger.info("Sent request to RO Extraction. Status code: %s",
                ro_request.status_code)

    return ro_request


def get_encoded_content_from_cas(r):
    content_decoded = r.content.decode('utf-8')
    encoded_bytes = base64.b64encode(
        content_decoded.encode("utf-8"))
    return str(encoded_bytes, "utf-8")


def get_cas_from_definitions_extract(input_cas_encoded):

    input_for_term_defined = {
        "cas_content": input_cas_encoded,
        "content_type": "html",
    }

    start = time.time()
    definitions_request = requests.post(DEFINITIONS_EXTRACT_URL,
                                        json=input_for_term_defined)
    end = time.time()
    logger.info("Sent request to DefinitionExtract NLP (%s) Status code: %s", DEFINITIONS_EXTRACT_URL,
                definitions_request.status_code)
    logger.info(
        "DefinitionExtract took %s seconds to succeed.", end - start)

    return definitions_request


def get_cas_from_text_extract(input_cas_encoded):
    text_cas = {
        "cas_content": input_cas_encoded,
        "content_type": "html",
        "extract_supergrams": "false"
    }
    start = time.time()
    request_nlp = requests.post(TERM_EXTRACT_URL, json=text_cas)
    end = time.time()
    logger.info(
        "Sent request to TextExtract NLP (%s). Status code: %s", TERM_EXTRACT_URL, request_nlp.status_code)
    logger.info(
        "TermExtract took %s seconds to succeed.", end - start)
    return request_nlp


@shared_task
def extract_reporting_obligations(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    core = 'documents'
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"

    q = "website:" + website_name + " AND acceptance_state:accepted"
    # q = "website:" + website_name + " AND content:* AND -content_html:[* TO *]"

    # Load all documents from Solr
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    options = {'rows': rows_per_page, 'start': page_number,
               'cursorMark': cursor_mark, 'sort': 'id asc', 'fl': 'content_html,content,id'}
    documents = client.search(q, **options)

    # Load typesystem
    ts = fetch_typesystem()

    for document in documents:
        logger.info("Started RO extraction for document id: %s", document['id'])

        is_html = False
        is_pdf = False
        r = None
        paragraph_request = None

        # Check if document is a html or pdf document
        if "content_html" in document:
            logger.info("Extracting terms from HTML document id: %s (%s chars)",
                        document['id'], len(document['content_html'][0]))
            is_html = True
        elif "content_html" not in document and "content" in document:
            logger.info("Extracting terms from PDF document id: %s (%s chars)",
                        document['id'], len(document['content'][0]))
            is_pdf = True

        if is_html:
            r = get_html2text_cas(document['content_html'][0])

        # Paragraph detection for PDF + fallback cas for not having a html2text request
        if is_pdf:
            r = get_cas_from_pdf(document['content'])
            paragraph_request = r

        encoded_b64 = get_encoded_content_from_cas(r)

        # Paragraph Detection for HTML
        if is_html:
            paragraph_request = get_cas_from_paragraph_detection(encoded_b64)

        # Send to RO API
        res = json.loads(paragraph_request.content.decode('utf-8'))
        ro_request = get_reporting_obligations(res['cas_content'])

        # Create new cas with sofa from RO API
        ro_cas = base64.b64decode( json.loads(ro_request.content)[ 'cas_content' ] ).decode( 'utf-8' )
        logger.info("ro_cas: %s", ro_cas)

        cas = load_cas_from_xmi(ro_cas, typesystem=ts)
        sofa_reporting_obligations = cas.get_view("ReportingObligationsView").sofa_string
        logger.info("sofa_reporting_obligations: %s", sofa_reporting_obligations)

        # Now send the CAS to UIMA Html2Text for the VBTT annotations (paragraph_request)
        r = get_html2text_cas(sofa_reporting_obligations)
        cas_html2text = load_cas_from_xmi(r.content.decode("utf-8"), typesystem=ts)

        logger.info("cas_html2text: %s", cas_html2text.to_xmi())

        # Read out the VBTT annotations
        for vbtt in cas.get_view(sofa_id_html2text).select(VALUE_BETWEEN_TAG_TYPE_CLASS):
            if vbtt.tagName == "p":
                logger.info("VBTT: %s", vbtt)
                logger.info("VBTT: %s", vbtt.get_covered_text())
        # TODO Remove break statement
        break


@shared_task
def extract_terms(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    core = 'documents'
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"

    q = "website:" + website_name + " AND acceptance_state:accepted"
    # q = "website:" + website_name + " AND content:* AND -content_html:[* TO *]"

    # Load all documents from Solr
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    options = {'rows': rows_per_page, 'start': page_number,
               'cursorMark': cursor_mark, 'sort': 'id asc', 'fl': 'content_html,content,id'}
    documents = client.search(q, **options)

    # Generate and write tempfile for typesystem.xml
    ts = fetch_typesystem()

    for document in documents:
        logger.info("Started term extraction for document id: %s", document['id'])
        django_doc = Document.objects.get(id=document['id'])
        r = None
        paragraph_request = None

        if "content_html" in document:
            logger.info("Extracting terms from HTML document id: %s (%s chars)",
                        document['id'], len(document['content_html'][0]))
            # Html2Text - Get XMI from UIMA - Only when HTML not for PDFs
            r = get_html2text_cas(document['content_html'][0])
            encoded_b64 = get_encoded_content_from_cas(r)
            # Paragraph Detection for HTML
            paragraph_request = get_cas_from_paragraph_detection(encoded_b64)

        elif "content_html" not in document and "content" in document:
            logger.info("Extracting terms from PDF document id: %s (%s chars)",
                        document['id'], len(document['content'][0]))
            # Paragraph detection for PDF + fallback cas for not having a html2text request
            r = get_cas_from_pdf(document['content'])
            paragraph_request = r

        # Term definition
        input_content = json.loads(paragraph_request.content)['cas_content']
        definitions_request = get_cas_from_definitions_extract(input_content)

        # Decoded cas from definitions extract
        definitions_decoded_cas = base64.b64decode(
            json.loads(definitions_request.content)['cas_content']).decode("utf-8")

        # Step 3: NLP TextExtract
        input_content = json.loads(definitions_request.content)['cas_content']
        request_nlp = get_cas_from_text_extract(input_content)

        # Decoded cas from termextract
        terms_decoded_cas = base64.b64decode(
            json.loads(request_nlp.content)['cas_content']).decode("utf-8")

        # Load CAS files from NLP
        cas = cassis.load_cas_from_xmi(
            definitions_decoded_cas, typesystem=ts)
        cas2 = cassis.load_cas_from_xmi(
            terms_decoded_cas, typesystem=ts)

        atomic_update_defined = [
            {
                "id": document['id'],
                "concept_defined": {"set": {
                    "v": "1",
                    "str": cas.get_view(sofa_id_html2text).sofa_string,
                    "tokens": [

                    ]
                }}
            }
        ]
        concept_defined_tokens = atomic_update_defined[0]['concept_defined']['set']['tokens']
        j = 0

        # Term defined, we check which terms are covered by definitions
        for defi in cas2.get_view(sofa_id_html2text).select(SENTENCE_CLASS):
            term_name = "Unknown"
            lemma_name = ""

            for i, term in enumerate(cas2.get_view(sofa_id_html2text).select_covered(TFIDF_CLASS, defi)):
                if i > 0:
                    logger.info("Found multiple terms: %s",
                                term.get_covered_text())
                    break

                term_name = term.get_covered_text()
                # Retrieve the lemma for the term
                for lemma in cas2.get_view(sofa_id_html2text).select_covered(LEMMA_CLASS, term):
                    if term.begin == lemma.begin and term.end == lemma.end:
                        lemma_name = lemma.value

            # Handle paragraphs
            for par in cas.get_view(sofa_id_html2text).select_covering(PARAGRAPH_CLASS, defi):

                if par.begin == defi.begin:  # if beginning of paragraph == beginning of a definition ==> this detected paragraph should replace the definition
                    defi = par

            token_defined = defi.get_covered_text()
            start_defined = defi.begin
            end_defined = defi.end

            # Step 7: Send concept terms to Solr ('concept_defined' field)

            if len(token_defined.encode('utf-8')) < 32000:
                token_to_add_defined = {
                    "t": token_defined,
                    "s": start_defined,
                    "e": end_defined,
                    "y": "word"
                }
                concept_defined_tokens.insert(j, token_to_add_defined)
                j = j + 1

                # Save Term Definitions in Django
                c = Concept.objects.update_or_create(
                    name=term_name, definition=defi.get_covered_text().strip(), lemma=lemma_name)
                ConceptDefined.objects.update_or_create(
                       concept=c[0], document= django_doc)
                # logger.info("Saved concept to django. name = %s, defi = %s", term_name, defi.get_covered_text())

        # Step 5: Send term extractions to Solr (term_occurs field)

        # Convert the output to a readable format for Solr
        atomic_update = [
            {
                "id": document['id'],
                "concept_occurs": {
                    "set": {
                        "v": "1",
                        "str": cas2.get_view(sofa_id_html2text).sofa_string,
                        "tokens": [

                        ]
                    }
                }
            }
        ]
        concept_occurs_tokens = atomic_update[0]['concept_occurs']['set']['tokens']

        # Select all Tfidfs from the CAS
        i = 0
        for term in cas2.get_view(sofa_id_html2text).select(TFIDF_CLASS):
            # Save the token information
            token = term.get_covered_text()
            score = term.tfidfValue
            start = term.begin
            end = term.end

            # Encode score base64
            encoded_bytes = base64.b64encode(score.encode("utf-8"))
            encoded_score = str(encoded_bytes, "utf-8")

            token_to_add = {
                "t": token,
                "s": start,
                "e": end,
                "y": "word",
                "p": encoded_score
            }
            concept_occurs_tokens.insert(i, token_to_add)
            i = i + 1

            # Retrieve the lemma for the term
            lemma_name = ""
            for lemma in cas2.get_view(sofa_id_html2text).select_covered(LEMMA_CLASS, term):
                if term.begin == lemma.begin and term.end == lemma.end:
                    lemma_name = lemma.value

            queryset = Concept.objects.filter(
                name=term.get_covered_text())
            if not queryset.exists():
                # Save Term Definitions in Django
                if (len(term.get_covered_text()) <= 200):
                   c = Concept.objects.update_or_create(
                        name=term.get_covered_text(), lemma=lemma_name)
                   ConceptOccurs.objects.update_or_create(
                       concept=c[0], document= django_doc, probability=float(score.encode("utf-8")) )
                     
                else:
                    logger.info("WARNING: Term '%s' has been skipped because the term name was too long. "
                                "Consider disabling supergrams or change the length in the database", token)

        # Step 6: Post term_occurs to Solr
        escaped_json = json.dumps(
            atomic_update[0]['concept_occurs']['set'])
        atomic_update[0]['concept_occurs']['set'] = escaped_json
        logger.info("Detected %s concepts", len(concept_occurs_tokens))
        if len(concept_occurs_tokens) > 0:
            post_pre_analyzed_to_solr(atomic_update)

        # Step 8: Post term_defined to Solr
        escaped_json_def = json.dumps(
            atomic_update_defined[0]['concept_defined']['set'])
        atomic_update_defined[0]['concept_defined']['set'] = escaped_json_def
        logger.info("Detected %s concept definitions",
                    len(concept_defined_tokens))
        if len(concept_defined_tokens) > 0:
            post_pre_analyzed_to_solr(atomic_update_defined)

        core = 'documents'
        requests.get(os.environ['SOLR_URL'] +
                     '/' + core + '/update?commit=true')

@shared_task
def score_documents_task(website_id, **kwargs):
    # lookup documents for website and score them
    website = Website.objects.get(pk=website_id)
    logger.info("Scoring documents with WEBSITE: " + website.name)
    solr_documents = solr_search_website_with_content(
        'documents', website.name, date=kwargs.get('date', None))
    use_pdf_files = True
    if website.name.lower() == 'eurlex':
        use_pdf_files = False
    score_documents(website.name, solr_documents, use_pdf_files)


@shared_task
def sync_documents_task(website_id, **kwargs):
    # lookup documents for website and sync them
    website = Website.objects.get(pk=website_id)
    logger.info("Syncing documents with WEBSITE: " + website.name)
    # query Solr for available documents and sync with Django

    date = kwargs.get('date', None)
    solr_documents = solr_search_website_sorted(
        core='documents', website=website.name.lower(), date=date)
    for solr_doc in solr_documents:
        solr_doc_date = solr_doc.get('date', [datetime.now()])[0]
        solr_doc_date_last_update = solr_doc.get(
            'date_last_update', datetime.now())
        # sanity check in case date_last_update was a solr array field
        if isinstance(solr_doc_date_last_update, list):
            solr_doc_date_last_update = solr_doc_date_last_update[0]
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
        # Update or create the document, this returns a tuple with the django document and a boolean indicating
        # whether or not the document was created
        current_doc, current_doc_created = Document.objects.update_or_create(
            id=solr_doc["id"], defaults=data)

    if not date:
        # check for outdated documents based on last time a document was found during scraping
        how_many_days = 30
        outdated_docs = Document.objects.filter(
            date_last_update__lte=datetime.now() - timedelta(days=how_many_days))
        up_to_date_docs = Document.objects.filter(
            date_last_update__gte=datetime.now() - timedelta(days=how_many_days))
        # tag documents that have not been updated in a while
        for doc in outdated_docs:
            try:
                Tag.objects.create(value="OFFLINE", document=doc)
            except ValidationError as e:
                # tag exists, skip
                logger.debug(str(e))
        # untag if the documents are now up to date
        for doc in up_to_date_docs:
            # fetch OFFLINE tag for this document
            try:
                offline_tag = Tag.objects.get(value="OFFLINE", document=doc)
                offline_tag.delete()
            except Tag.DoesNotExist:
                # OFFLINE tag not found, skip
                pass


@shared_task
def delete_documents_not_in_solr_task(website_id):
    website = Website.objects.get(pk=website_id)
    # query Solr for available documents
    solr_documents = solr_search_website_sorted(
        core='documents', website=website.name.lower())
    # delete django Documents that no longer exist in Solr
    django_documents = list(Document.objects.filter(website=website))
    django_doc_ids = [str(django_doc.id) for django_doc in django_documents]
    solr_doc_ids = [solr_doc["id"] for solr_doc in solr_documents]
    to_delete_doc_ids = set(django_doc_ids) - set(solr_doc_ids)
    to_delete_docs = Document.objects.filter(pk__in=to_delete_doc_ids)
    logger.info('Deleting deprecated documents...')
    to_delete_docs.delete()


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
def parse_content_to_plaintext_task(website_id, **kwargs):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    logger.info('Adding content to each %s document.', website_name)
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"
    date = kwargs.get('date', None)
    # Make sure solr index is updated
    core = 'documents'
    requests.get(os.environ['SOLR_URL'] +
                 '/' + core + '/update?commit=true')
    # select all records where content is empty and content_html is not

    q = "-content: [\"\" TO *] AND ( content_html: [* TO *] OR file_name: [* TO *] ) AND website:" + website_name
    if date:
        q = q + " AND date:[" + date + " TO NOW]"  # eg. 2013-07-17T00:00:00Z

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
                    for d in file_data.stream(32 * 1024):
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


def is_document_english(plain_text):
    english = False
    detect_threshold = 0.4
    try:
        langs = detect_langs(plain_text)
        number_langs = len(langs)
        # trivial case for 1 language detected
        if number_langs == 1:
            if langs[0].lang == 'en':
                english = True
        # if 2 or more languages are detected, consider detect probability
        else:
            for detected in langs:
                if detected.lang == 'en' and detected.prob >= detect_threshold:
                    english = True
                    break
    except LangDetectException:
        pass
    return english


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
            for d in file_data.stream(32 * 1024):
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


@shared_task
def check_documents_unvalidated_task(website_id):
    website = Website.objects.get(pk=website_id)
    logger.info(
        "Set unvalidated field for all documents for website: %s", str(website))
    docs = Document.objects.filter(website=website)
    for doc in docs:
        # get all acceptance states that are not unvalidated
        validated_states = AcceptanceState.objects.filter(document=doc).exclude(
            value=AcceptanceStateValue.UNVALIDATED)
        # update document unvalidated state accordingly
        if not validated_states:
            doc.unvalidated = True
        else:
            doc.unvalidated = False
        doc.save()


def create_bucket(client, name):
    try:
        client.make_bucket(name)
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass
