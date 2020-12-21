import time
import base64
import json
import logging
import os
import urllib
import pysolr
import cassis
import requests
import math

from cassis import Cas, load_cas_from_xmi
from cassis.typesystem import load_typesystem
from celery import shared_task, chain
from glossary.models import Concept, ConceptOccurs, ConceptDefined
from searchapp.models import Website, Document
from obligations.models import ReportingObligation

logger = logging.getLogger(__name__)

# TODO Theres already a solr defined
SOLR_URL = os.environ['SOLR_URL']
# Don't remove the '/' at the end here
TERM_EXTRACT_URL = os.environ['GLOSSARY_TERM_EXTRACT_URL']
DEFINITIONS_EXTRACT_URL = os.environ['GLOSSARY_DEFINITIONS_EXTRACT_URL']
PARAGRAPH_DETECT_URL = os.environ['GLOSSARY_PARAGRAPH_DETECT_URL']
RO_EXTRACT_URL = os.environ['RO_EXTRACT_URL']
CAS_TO_RDF_API = os.environ['CAS_TO_RDF_API']
CELERY_EXTRACT_TERMS_CHUNKS = os.environ.get('CELERY_EXTRACT_TERMS_CHUNKS', 8)
EXTRACT_TERMS_NLP_VERSION = os.environ.get(
    'EXTRACT_TERMS_NLP_VERSION', '8a4f1d58')

SENTENCE_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
TFIDF_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.frequency.tfidf.type.Tfidf"
LEMMA_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"
PARAGRAPH_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph"
VALUE_BETWEEN_TAG_TYPE_CLASS = "com.crosslang.uimahtmltotext.uima.type.ValueBetweenTagType"

DEFAULT_TYPESYSTEM = "typesystem_tmp.xml"

sofa_id_html2text = "html2textView"
sofa_id_text2html = "text2htmlView"
UIMA_URL = {"BASE": os.environ['GLOSSARY_UIMA_URL'],  # http://uima:8008
            "HTML2TEXT": "/html2text",
            "TEXT2HTML": "/text2html",
            "TYPESYSTEM": "/html2text/typesystem",
            }

CONST_UPDATE_WITH_COMMIT = "/update?commit=true"
CONST_EXPORT = '/export/'
QUERY_ID_ASC = 'id asc'
QUERY_WEBSITE = "website:"


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


def save_to_rdf(cas):
    encoded_cas = base64.b64encode(bytes(cas.to_xmi(), 'utf-8')).decode()

    json_content = {
        "content": encoded_cas
    }

    logger.info("base64 cas (ROs): %s", encoded_cas)

    start = time.time()
    r = requests.post(CAS_TO_RDF_API, json=json_content)
    end = time.time()
    logger.info('Sent request to %s. Status code: %s Took %s seconds', CAS_TO_RDF_API,
                r.status_code, end-start)
    return r


def create_cas(sofa):
    with open(DEFAULT_TYPESYSTEM, 'rb') as f:
        ts = load_typesystem(f)

    cas = Cas(typesystem=ts)
    cas.sofa_string = sofa
    return cas


def fetch_typesystem():
    typesystem_req = requests.get(
        UIMA_URL["BASE"] + UIMA_URL["TYPESYSTEM"])
    typesystem_file = open(DEFAULT_TYPESYSTEM, "w")
    typesystem_file.write(typesystem_req.content.decode("utf-8"))
    with open(DEFAULT_TYPESYSTEM, 'rb') as f:
        return load_typesystem(f)


def get_cas_from_pdf(content):
    logger.info("PDF: get_cas_from_pdf() called: content is: %s", content)
    # Logic for documents without HTML, that have a "content" field which is a PDF to HTML done by Tika
    # Create a new cas here
    start = time.time()
    tika_cas = create_cas(content)

    encoded_cas = base64.b64encode(bytes(tika_cas.to_xmi(), 'utf-8')).decode()

    logger.info("PDF: encoded_cas: %s", encoded_cas)

    # Then send this cas to NLP Paragraph detection
    input_for_paragraph_detection = {
        "cas_content": encoded_cas,
        "content_type": "pdf",
    }

    logger.info("PDF: input_for_paragraph_detection: %s",
                input_for_paragraph_detection)

    r = requests.post(PARAGRAPH_DETECT_URL,
                      json=input_for_paragraph_detection)
    logger.info("Sent request to Paragraph Detection (%s). Status code: %s", PARAGRAPH_DETECT_URL,
                r.status_code)
    end = time.time()
    logger.info(
        "Paragraph Detect took %s seconds to succeed.", end - start)
    return r


def get_cas_from_paragraph_detection(content_encoded):
    input_for_paragraph_detection = {
        "cas_content": content_encoded,
        "content_type": "html",
    }

    start = time.time()
    paragraph_request = requests.post(PARAGRAPH_DETECT_URL,
                                      json=input_for_paragraph_detection)
    logger.info("Sent request to Paragraph Detection (%s). Status code: %s", PARAGRAPH_DETECT_URL,
                paragraph_request.status_code)

    end = time.time()
    logger.info(
        "Paragraph Detect took %s seconds to succeed.", end - start)
    return paragraph_request


def get_reporting_obligations(input_cas_encoded):
    input_for_reporting_obligations = {
        "cas_content": input_cas_encoded,
        "content_type": "html",
    }

    start = time.time()
    ro_request = requests.post(RO_EXTRACT_URL,
                               json=input_for_reporting_obligations)
    end = time.time()
    logger.info("Sent request to RO Extraction. Status code: %s Took % seconds",
                ro_request.status_code, end-start)

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


def post_pre_analyzed_to_solr(data):
    params = json.dumps(data).encode('utf8')
    req = urllib.request.Request(os.environ['SOLR_URL'] + "/documents/update", data=params,
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    logger.info(response.read().decode('utf8'))


@shared_task
def extract_reporting_obligations(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    core = 'documents'
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"

    q = QUERY_WEBSITE + website_name + " AND acceptance_state:accepted"

    # Load all documents from Solr
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    options = {'rows': rows_per_page, 'start': page_number,
               'cursorMark': cursor_mark, 'sort': QUERY_ID_ASC, 'fl': 'content_html,content,id'}
    documents = client.search(q, **options)

    # Load typesystem
    ts = fetch_typesystem()

    for document in documents:
        logger.info("Started RO extraction for document id: %s",
                    document['id'])

        is_html = False
        is_pdf = False
        r = None
        paragraph_request = None

        # Check if document is a html or pdf document
        if "content_html" in document:
            logger.info("Extracting terms from HTML document id: %s (%s chars)",
                        document['id'], len(document['content_html'][0]))
            is_html = True

            logger.warning("SKIPPING HTML TO TEST PDFS")
            continue
        elif "content_html" not in document and "content" in document:
            logger.info("Extracting terms from PDF document id: %s (%s chars)",
                        document['id'], len(document['content'][0]))
            is_pdf = True

            # TODO Remove this later when pdf works
            #logger.warning("PDF CURRENTLY NOT SUPPORTED, SKIPPED.")
            # continue

        if is_html:
            r = get_html2text_cas(document['content_html'][0])

        # Paragraph detection for PDF + fallback cas for not having a html2text request
        if is_pdf:
            r = get_cas_from_pdf(document['content'][0])
            paragraph_request = r

        encoded_b64 = get_encoded_content_from_cas(r)

        # Paragraph Detection for HTML
        if is_html:
            paragraph_request = get_cas_from_paragraph_detection(encoded_b64)

        # Send to RO API
        res = json.loads(paragraph_request.content.decode('utf-8'))
        ro_request = get_reporting_obligations(res['cas_content'])

        # Create new cas with sofa from RO API
        if ro_request.status_code == 200:
            ro_cas = base64.b64decode(json.loads(ro_request.content)[
                                      'cas_content']).decode('utf-8')
            #logger.info("ro_cas: %s", ro_cas)

            cas = load_cas_from_xmi(ro_cas, typesystem=ts)
            sofa_reporting_obligations = cas.get_view(
                "ReportingObligationsView").sofa_string
            # logger.info("sofa_reporting_obligations: %s",sofa_reporting_obligations)

            # Now send the CAS to UIMA Html2Text for the VBTT annotations (paragraph_request)
            r = get_html2text_cas(sofa_reporting_obligations)
            cas_html2text = load_cas_from_xmi(
                r.content.decode("utf-8"), typesystem=ts)

            # This is the CAS with reporting obligations wrapped in VBTT's
            # logger.info("cas_html2text: %s", cas_html2text.to_xmi())

            # Save RO's to Django
            for vbtt in cas_html2text.get_view(sofa_id_html2text).select(VALUE_BETWEEN_TAG_TYPE_CLASS):
                if vbtt.tagName == "p":
                    # Save to Django
                    ReportingObligation.objects.update_or_create(
                        name=vbtt.get_covered_text(), definition=vbtt.get_covered_text())
                    logger.info(
                        "[CAS] Saved Reporting Obligation to Django: %s", vbtt.get_covered_text())

            # Send CAS to Laurens API

            r = save_to_rdf(cas_html2text)
            if r.status_code == 200:
                rdf_json = r.json()

                logger.info("rdf_json: %s", rdf_json)

                for item in rdf_json['children']:
                    rdf_value = item['value']
                    rdf_id = item['id']

                    ReportingObligation.objects.update_or_create(
                        name=rdf_value, definition=rdf_value, defaults={'rdf_id': rdf_id})
                    logger.info(
                        "[RDF] Saved Reporting Obligation to Django: %s", rdf_value)
            else:
                logger.info(
                    "[RDF]: Failed to save CAS to RDF. Response code: %s", r.status_code)


@shared_task
def extract_terms(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    core = 'documents'
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"

    # select all accepted documents with empty concept_occurs field
    q = QUERY_WEBSITE + website_name + \
        " AND acceptance_state: accepted AND -concept_occurs: [\"\" TO *] "

    # Load all documents from Solr
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    options = {'rows': rows_per_page, 'start': page_number,
               'cursorMark': cursor_mark, 'sort': QUERY_ID_ASC, 'fl': 'content_html,content,id'}
    documents = client.search(q, **options)

    # Divide the document in chunks
    extract_terms_for_document.chunks(
        zip(documents), CELERY_EXTRACT_TERMS_CHUNKS).delay()

    requests.get(os.environ['SOLR_URL'] +
                 '/' + core + CONST_UPDATE_WITH_COMMIT)


# Generate and write tempfile for typesystem.xml
# FIXME: find a way of passing this to the extract_terms_for_document() method ?
typesystem = fetch_typesystem()


@shared_task
def extract_terms_for_document(document):

    logger.info("Started term extraction for document id: %s", document['id'])
    # Generate and write tempfile for typesystem.xml
    ts = fetch_typesystem()
    django_doc = Document.objects.get(id=document['id'])
    r = None
    paragraph_request = None

    if "content_html" in document:
        if document['content_html'] is not None:
            if len(document['content_html'][0]) > 1000000:
                logger.info("Skipping too big document id: %s", document['id'])
                return

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
        r = get_cas_from_pdf(document['content'][0])
        paragraph_request = r

    # Term definition
    input_content = json.loads(paragraph_request.content)['cas_content']
    definitions_request = get_cas_from_definitions_extract(input_content)

    # Step 3: NLP TextExtract
    input_content = json.loads(definitions_request.content)['cas_content']
    request_nlp = get_cas_from_text_extract(input_content)

    # Decoded cas from termextract
    terms_decoded_cas = base64.b64decode(
        json.loads(request_nlp.content)['cas_content']).decode("utf-8")

    # Load CAS files from NLP
    cas2 = cassis.load_cas_from_xmi(
        terms_decoded_cas, typesystem=typesystem)

    atomic_update_defined = [
        {
            "id": document['id'],
            "concept_defined": {"set": {
                "v": "1",
                "str": cas2.get_view(sofa_id_html2text).sofa_string,
                "tokens": [

                ]
            }}
        }
    ]
    concept_defined_tokens = atomic_update_defined[0]['concept_defined']['set']['tokens']
    j = 0

    # Term defined, we check which terms are covered by definitions
    term_definition = []
    term_definition_uniq = []
    term_definition_uniq_idx = []
    for sentence in cas2.get_view('html2textView').select(SENTENCE_CLASS):
        has_term_defined = False
        for token in cas2.get_view('html2textView').select_covered('cassis.Token', sentence):
            # take those tfidf annotations with a cassis.token annotation covering them ==> the terms defined in the definition
            for term_defined in cas2.get_view('html2textView').select_covering(TFIDF_CLASS, token):
                if (term_defined.begin == token.begin) and (term_defined.end == token.end):
                    # instead of saving sentence, save sentence + context (i.e. paragraph annotation)
                    for par in cas2.get_view(sofa_id_html2text).select_covering(PARAGRAPH_CLASS, sentence):
                        if par.begin == sentence.begin:  # if beginning of paragraph == beginning of a definition ==> this detected paragraph should replace the definition
                            sentence = par
                    term_definition.append((term_defined, sentence))
                    has_term_defined = True
        if has_term_defined and sentence.begin not in term_definition_uniq_idx:
            term_definition_uniq.append(sentence)
            term_definition_uniq_idx.append(sentence.begin)

    # For solr
    for definition in term_definition_uniq:
        token_defined = definition.get_covered_text()
        start_defined = definition.begin
        end_defined = definition.end

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

    # For django
    for term, definition in term_definition:
        lemma_name = ""
        token_defined = definition.get_covered_text()
        start_defined = definition.begin
        end_defined = definition.end

        if len(token_defined.encode('utf-8')) < 32000:
            if len(term.get_covered_text()) <= 200:
                # Save Term Definitions in Django
                c = Concept.objects.update_or_create(
                    name=term.get_covered_text(), definition=token_defined, lemma=lemma_name, version=EXTRACT_TERMS_NLP_VERSION)
                # logger.info("Saved concept to django. name = %s, defi = %s (%s:%s)", term.term, definition.get_covered_text(), start_defined, end_defined)
                defs = ConceptDefined.objects.filter(
                    concept=c[0], document=django_doc)
                if len(defs) == 1:
                    cd = defs[0]
                    cd.begin = start_defined
                    cd.end = end_defined
                    cd.save()
                else:
                    ConceptDefined.objects.create(
                        concept=c[0], document=django_doc, begin=start_defined, end=end_defined)
            else:
                logger.info("WARNING: Term '%s' has been skipped because the term name was too long. "
                            "Consider disabling supergrams or change the length in the database", token)

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
            if len(term.get_covered_text()) <= 200:
                c = Concept.objects.update_or_create(
                    name=term.get_covered_text(), lemma=lemma_name, version=EXTRACT_TERMS_NLP_VERSION)
                ConceptOccurs.objects.update_or_create(
                    concept=c[0], document=django_doc, probability=float(score.encode("utf-8")), begin=start,
                    end=end)

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
