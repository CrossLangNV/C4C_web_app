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
import gzip

from cassis import Cas, load_cas_from_xmi, TypeSystem, merge_typesystems, load_dkpro_core_typesystem
from cassis.typesystem import load_typesystem
from celery import shared_task, chain
from glossary.models import Concept, ConceptOccurs, ConceptDefined
from searchapp.models import Website, Document
from obligations.models import ReportingObligation
from minio import Minio, ResponseError
from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists, NoSuchKey
from pycaprio.mappings import InceptionFormat, DocumentState
from pycaprio import Pycaprio

from glossary.models import AnnotationWorklog
from cpsv.cpsv_rdf_call import get_contact_points, get_public_services, get_contact_point_info, get_graphs

from cpsv.models import PublicService, ContactPoint

logger = logging.getLogger(__name__)

# TODO Theres already a solr defined
SOLR_URL = os.environ["SOLR_URL"]
# Don't remove the '/' at the end here
TERM_EXTRACT_URL = os.environ["GLOSSARY_TERM_EXTRACT_URL"]
DEFINITIONS_EXTRACT_URL = os.environ["GLOSSARY_DEFINITIONS_EXTRACT_URL"]
PARAGRAPH_DETECT_URL = os.environ["GLOSSARY_PARAGRAPH_DETECT_URL"]
RO_EXTRACT_URL = os.environ["RO_EXTRACT_URL"]
CAS_TO_RDF_API = os.environ["CAS_TO_RDF_API"]
CELERY_EXTRACT_TERMS_CHUNKS = os.environ.get("CELERY_EXTRACT_TERMS_CHUNKS", 8)
EXTRACT_TERMS_NLP_VERSION = os.environ.get("EXTRACT_TERMS_NLP_VERSION", "8a4f1d58")
EXTRACT_RO_NLP_VERSION = os.environ.get("EXTRACT_RO_NLP_VERSION", "d16bba97890")

SENTENCE_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
TOKEN_CLASS = "cassis.Token"
TFIDF_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.frequency.tfidf.type.Tfidf"
LEMMA_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"
PARAGRAPH_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph"
VALUE_BETWEEN_TAG_TYPE_CLASS = "com.crosslang.uimahtmltotext.uima.type.ValueBetweenTagType"
DEPENDENCY_CLASS = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency"
DEFINED_TYPE = "cassis.Token"

DEFAULT_TYPESYSTEM = "/tmp/typesystem.xml"
TYPESYSTEM_USER = "scheduler/resources/typesystem_user.xml"

sofa_id_html2text = "html2textView"
sofa_id_text2html = "text2htmlView"
UIMA_URL = {
    "BASE": os.environ["GLOSSARY_UIMA_URL"],  # http://uima:8008
    "HTML2TEXT": "/html2text",
    "TEXT2HTML": "/text2html",
    "TYPESYSTEM": "/html2text/typesystem",
}

CONST_EXPORT = "/export/"
QUERY_ID_ASC = "id asc"
QUERY_WEBSITE = "website:"

RDF_FUSEKI_URL = os.environ["RDF_FUSEKI_URL"]


def save_cas(cas, file_path):
    cas_xmi = cas.to_xmi(pretty_print=True)
    with open(file_path, "wb") as f:
        f.write(cas_xmi.encode())


def save_typesystem(typesystem, file_path):
    ts_xml = typesystem.to_xml()
    with open(file_path, "wb") as f:
        f.write(ts_xml.encode())


def save_compressed_cas(cas, file_path):
    cas_xmi = cas.to_xmi()
    file = gzip.open(file_path, "wb")
    file.write(cas_xmi.encode())
    file.close()
    return file


def load_compressed_cas(file, typesystem):
    with gzip.open(file, "rb") as f:
        return load_cas_from_xmi(f, typesystem=typesystem)


def get_html2text_cas(content_html, docid):
    content_html_text = {"text": content_html}
    logger.info("Sending request to %s", UIMA_URL["BASE"] + UIMA_URL["HTML2TEXT"])
    start = time.time()
    r = requests.post(UIMA_URL["BASE"] + UIMA_URL["HTML2TEXT"], json=content_html_text)

    end = time.time()
    logger.info("UIMA Html2Text took %s seconds to succeed (code %s ) (id: %s ).", end - start, r.status_code, docid)
    return r


def save_to_rdf(cas):
    encoded_cas = base64.b64encode(bytes(cas.to_xmi(), "utf-8")).decode()

    json_content = {"content": encoded_cas}

    logger.info("base64 cas (ROs): %s", encoded_cas)

    start = time.time()
    r = requests.post(CAS_TO_RDF_API, json=json_content)
    end = time.time()
    logger.info("Sent request to %s. Status code: %s Took %s seconds", CAS_TO_RDF_API, r.status_code, end - start)
    return r


def create_cas(sofa):
    with open(DEFAULT_TYPESYSTEM, "rb") as f:
        ts = load_typesystem(f)

    cas = Cas(typesystem=ts)
    cas.sofa_string = sofa
    return cas


def fetch_typesystem():
    try:
        # Check if file exits
        f = open(DEFAULT_TYPESYSTEM)
        f.close()
    except IOError:
        # Fetch from UIMA
        typesystem_req = requests.get(UIMA_URL["BASE"] + UIMA_URL["TYPESYSTEM"])
        typesystem_file = open(DEFAULT_TYPESYSTEM, "w")
        typesystem_file.write(typesystem_req.content.decode("utf-8"))

    # FIXME: load only once ?
    with open(DEFAULT_TYPESYSTEM, "rb") as f:
        return load_typesystem(f)


def get_cas_from_pdf(content, docid):
    # Logic for documents without HTML, that have a "content" field which is a PDF to HTML done by Tika
    # Create a new cas here
    start = time.time()
    tika_cas = create_cas(content)

    encoded_cas = base64.b64encode(bytes(tika_cas.to_xmi(), "utf-8")).decode()

    # Then send this cas to NLP Paragraph detection
    input_for_paragraph_detection = {
        "cas_content": encoded_cas,
        "content_type": "pdf",
    }

    logger.info("Sending request to Paragraph Detection (PDF) (%s)", PARAGRAPH_DETECT_URL)
    logger.info("input_for_paragraph_detection: %s", input_for_paragraph_detection)
    r = requests.post(PARAGRAPH_DETECT_URL, json=input_for_paragraph_detection)
    end = time.time()
    logger.info("Paragraph Detect took %s seconds to succeed (code: %s) (id: %s).", end - start, r.status_code, docid)
    logger.info("Output: %s", r.content)
    return r


def get_cas_from_paragraph_detection(content_encoded, docid):
    input_for_paragraph_detection = {
        "cas_content": content_encoded,
        "content_type": "html",
    }

    logger.info("Sending request to Paragraph Detection (HTML) (%s)", PARAGRAPH_DETECT_URL)
    start = time.time()
    paragraph_request = requests.post(PARAGRAPH_DETECT_URL, json=input_for_paragraph_detection)
    end = time.time()
    logger.info(
        "Paragraph Detect took %s seconds to succeed (code: %s) (id: %s).",
        end - start,
        paragraph_request.status_code,
        docid,
    )
    return paragraph_request


def get_reporting_obligations(input_cas_encoded):
    input_for_reporting_obligations = {
        "cas_content": input_cas_encoded,
        "content_type": "html",
    }

    start = time.time()
    ro_request = requests.post(RO_EXTRACT_URL, json=input_for_reporting_obligations)
    end = time.time()
    logger.info("Sent request to RO Extraction. Status code: %s Took % seconds", ro_request.status_code, end - start)

    return ro_request


def get_encoded_content_from_cas(r):
    content_decoded = r.content.decode("utf-8")
    encoded_bytes = base64.b64encode(content_decoded.encode("utf-8"))
    return str(encoded_bytes, "utf-8")


def get_cas_from_definitions_extract(input_cas_encoded, docid):
    input_for_term_defined = {
        "cas_content": input_cas_encoded,
        "content_type": "html",
    }

    logger.info("Sending request to DefinitionExtract NLP (%s)", DEFINITIONS_EXTRACT_URL)
    start = time.time()
    definitions_request = requests.post(DEFINITIONS_EXTRACT_URL, json=input_for_term_defined)
    end = time.time()
    logger.info(
        "DefinitionExtract took %s seconds to succeed (code: %s) (id: %s).",
        end - start,
        definitions_request.status_code,
        docid,
    )

    return definitions_request


def get_cas_from_text_extract(input_cas_encoded, docid):
    text_cas = {"cas_content": input_cas_encoded, "content_type": "html", "extract_supergrams": "false"}
    logger.info("Sending request to TextExtract NLP (%s)", TERM_EXTRACT_URL)
    start = time.time()
    request_nlp = requests.post(TERM_EXTRACT_URL, json=text_cas)
    end = time.time()
    logger.info(
        "TermExtract took %s seconds to succeed (code: %s) (id: %s).", end - start, request_nlp.status_code, docid
    )
    return request_nlp


def post_pre_analyzed_to_solr(data):
    params = json.dumps(data).encode("utf8")
    # FIXME: find a way to commit when all the work is done, commits after 15s now
    req = urllib.request.Request(
        os.environ["SOLR_URL"] + "/documents/update?commitWithin=15000",
        data=params,
        headers={"content-type": "application/json"},
    )
    response = urllib.request.urlopen(req)
    logger.info(response.read().decode("utf8"))


@shared_task
def extract_reporting_obligations(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    core = "documents"
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"

    q = QUERY_WEBSITE + website_name
    # q = QUERY_WEBSITE + website_name + " AND acceptance_state:accepted"

    # Load all documents from Solr
    client = pysolr.Solr(os.environ["SOLR_URL"] + "/" + core)
    options = {
        "rows": rows_per_page,
        "start": page_number,
        "cursorMark": cursor_mark,
        "sort": QUERY_ID_ASC,
        "fl": "content_html,content,id",
    }
    documents = client.search(q, **options)

    # Load typesystem
    ts = fetch_typesystem()

    for document in documents:
        logger.info("Started RO extraction for document id: %s", document["id"])

        is_html = False
        is_pdf = False
        r = None
        paragraph_request = None

        # Check if document is a html or pdf document
        if "content_html" in document:
            logger.info(
                "Extracting terms from HTML document id: %s (%s chars)",
                document["id"],
                len(document["content_html"][0]),
            )
            is_html = True

        elif "content_html" not in document and "content" in document:
            logger.info(
                "Extracting terms from PDF document id: %s (%s chars)", document["id"], len(document["content"][0])
            )
            is_pdf = True

            # TODO Remove this later when pdf works
            # logger.warning("PDF CURRENTLY NOT SUPPORTED, SKIPPED.")
            # continue

        if is_html:
            r = get_html2text_cas(document["content_html"][0])

        # Paragraph detection for PDF + fallback cas for not having a html2text request
        if is_pdf:
            logger.info("get_cas_from_pdf")
            r = get_cas_from_pdf(document["content"][0], document["id"])
            paragraph_request = r

        logger.info("")
        encoded_b64 = get_encoded_content_from_cas(r)

        # Paragraph Detection for HTML
        if is_html:
            paragraph_request = get_cas_from_paragraph_detection(encoded_b64)

        if not paragraph_request.content["cas_content"]:
            logger.error("Something went wrong in paragraph detection.")
            continue

        # Send to RO API
        res = json.loads(paragraph_request.content.decode("utf-8"))
        ro_request = get_reporting_obligations(res["cas_content"])

        # Create new cas with sofa from RO API
        if ro_request.status_code == 200:
            ro_cas = base64.b64decode(json.loads(ro_request.content)["cas_content"]).decode("utf-8")
            # logger.info("ro_cas: %s", ro_cas)

            cas = load_cas_from_xmi(ro_cas, typesystem=ts)
            sofa_reporting_obligations = cas.get_view("ReportingObligationsView").sofa_string

            logger.info("sofa_reporting_obligations: %s", sofa_reporting_obligations)
            # Save the HTML view of the reporting obligations
            # Save CAS to MINIO
            minio_client = Minio(
                os.environ["MINIO_STORAGE_ENDPOINT"],
                access_key=os.environ["MINIO_ACCESS_KEY"],
                secret_key=os.environ["MINIO_SECRET_KEY"],
                secure=False,
            )
            bucket_name = "ro-html-output"
            try:
                minio_client.make_bucket(bucket_name)
            except BucketAlreadyOwnedByYou as err:
                pass
            except BucketAlreadyExists as err:
                pass

            logger.info("Created bucket: %s", bucket_name)
            filename = document["id"] + "-" + EXTRACT_RO_NLP_VERSION + ".html"

            html_file = open(filename, "w")
            html_file.write(sofa_reporting_obligations)
            html_file.close()

            minio_client.fput_object(bucket_name, html_file.name, filename, "text/html; charset=UTF-8")
            logger.info("Uploaded to minio")

            os.remove(html_file.name)
            logger.info("Removed file from system")

            # Now send the CAS to UIMA Html2Text for the VBTT annotations (paragraph_request)
            r = get_html2text_cas(sofa_reporting_obligations, document["id"])
            cas_html2text = load_cas_from_xmi(r.content.decode("utf-8"), typesystem=ts)

            # This is the CAS with reporting obligations wrapped in VBTT's
            # logger.info("cas_html2text: %s", cas_html2text.to_xmi())

            # Save RO's to Django
            for vbtt in cas_html2text.get_view(sofa_id_html2text).select(VALUE_BETWEEN_TAG_TYPE_CLASS):
                if vbtt.tagName == "p":
                    # Save to Django
                    ReportingObligation.objects.update_or_create(
                        name=vbtt.get_covered_text(), definition=vbtt.get_covered_text()
                    )
                    logger.info("[CAS] Saved Reporting Obligation to Django: %s", vbtt.get_covered_text())

            # Send CAS to Laurens API

            r = save_to_rdf(cas_html2text)
            if r.status_code == 200:
                rdf_json = r.json()

                logger.info("rdf_json: %s", rdf_json)

                for item in rdf_json["children"]:
                    rdf_value = item["value"]
                    rdf_id = item["id"]

                    ReportingObligation.objects.update_or_create(
                        name=rdf_value, definition=rdf_value, defaults={"rdf_id": rdf_id}
                    )
                    logger.info("[RDF] Saved Reporting Obligation to Django: %s", rdf_value)
            else:
                logger.info("[RDF]: Failed to save CAS to RDF. Response code: %s", r.status_code)


@shared_task
def extract_terms(website_id, document_id=None):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    core = "documents"
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"

    if document_id:
        q = "id:" + document_id
        logger.info("Extract terms task, DOCUMENT: %s", document_id)
    else:
        logger.info("Extract terms task, WEBSITE: %s", website)
        # select all accepted documents with empty concept_occurs field
        q = QUERY_WEBSITE + website_name + ' AND acceptance_state:accepted AND -concept_occurs: ["" TO *]'

    # Load all documents from Solr
    client = pysolr.Solr(os.environ["SOLR_URL"] + "/" + core)
    options = {
        "rows": rows_per_page,
        "start": page_number,
        "cursorMark": cursor_mark,
        "sort": QUERY_ID_ASC,
        "fl": "content_html,content,id",
    }
    documents = client.search(q, **options)

    # Divide the document in chunks
    extract_terms_for_document.chunks(zip(documents), int(CELERY_EXTRACT_TERMS_CHUNKS)).delay()


@shared_task
def extract_terms_for_document(document):

    logger.info("Started term extraction for document id: %s", document["id"])

    # Load fisma specific types
    ts_fisma = generate_typesystem_fisma()
    term_type = ts_fisma.get_type("com.crosslang.fisma.Term")
    definition_type = ts_fisma.get_type("com.crosslang.fisma.Definition")
    defiterm_type = ts_fisma.get_type("com.crosslang.fisma.DefinitionTerm")

    # Generate and write tempfile for typesystem.xml
    typesystem = merge_typesystems(ts_fisma, fetch_typesystem())

    django_doc = Document.objects.get(id=document["id"])
    r = None
    paragraph_request = None

    if "content_html" in document:
        if document["content_html"] is not None:
            if len(document["content_html"][0]) > 1000000:
                logger.info("Skipping too big document id: %s", document["id"])
                return

        logger.info(
            "Extracting terms from HTML document id: %s (%s chars)", document["id"], len(document["content_html"][0])
        )
        # Html2Text - Get XMI from UIMA - Only when HTML not for PDFs
        r = get_html2text_cas(document["content_html"][0], django_doc.id)
        encoded_b64 = get_encoded_content_from_cas(r)
        # Paragraph Detection for HTML
        paragraph_request = get_cas_from_paragraph_detection(encoded_b64, django_doc.id)

    elif "content_html" not in document and "content" in document:
        logger.info(
            "Extracting terms from PDF document id: %s (%s chars)", document["id"], len(document["content"][0])
        )
        # Paragraph detection for PDF + fallback cas for not having a html2text request
        r = get_cas_from_pdf(document["content"][0], django_doc.id)
        paragraph_request = r

    # Term definition
    input_content = json.loads(paragraph_request.content)["cas_content"]
    definitions_request = get_cas_from_definitions_extract(input_content, django_doc.id)

    # Step 3: NLP TextExtract
    input_content = json.loads(definitions_request.content)["cas_content"]
    request_nlp = get_cas_from_text_extract(input_content, django_doc.id)

    # Decoded cas from termextract
    terms_decoded_cas = base64.b64decode(json.loads(request_nlp.content)["cas_content"]).decode("utf-8")

    # Load CAS files from NLP
    cas2 = cassis.load_cas_from_xmi(terms_decoded_cas, typesystem=typesystem)

    atomic_update_defined = [
        {
            "id": document["id"],
            "concept_defined": {"set": {"v": "1", "str": cas2.get_view(sofa_id_html2text).sofa_string, "tokens": []}},
        }
    ]
    concept_defined_tokens = atomic_update_defined[0]["concept_defined"]["set"]["tokens"]
    j = 0

    start_cas = time.time()
    # Term defined, we check which terms are covered by definitions
    definitions = []
    term_definition_uniq = []
    term_definition_uniq_idx = []
    # Each sentence is a definiton
    for sentence in cas2.get_view("html2textView").select(SENTENCE_CLASS):
        term_definitions = []
        # Instead of saving sentence, save sentence + context (i.e. paragraph annotation)
        for par in cas2.get_view(sofa_id_html2text).select_covering(PARAGRAPH_CLASS, sentence):
            if (
                par.begin == sentence.begin
            ):  # if beginning of paragraph == beginning of a definition ==> this detected paragraph should replace the definition
                sentence = par
        logger.debug("Found definition: %s", sentence.get_covered_text()[0:200])
        cas2.get_view(sofa_id_html2text).add_annotation(definition_type(begin=sentence.begin, end=sentence.end))
        # Find terms in definitions
        for token in cas2.get_view("html2textView").select_covered(TOKEN_CLASS, sentence):
            # take those tfidf annotations with a cassis.token annotation covering them ==> the terms defined in the definition
            for term_defined in cas2.get_view("html2textView").select_covering(TFIDF_CLASS, token):
                if (term_defined.begin == token.begin) and (term_defined.end == token.end):
                    term_definitions.append((term_defined, sentence))
                    cas2.get_view(sofa_id_html2text).add_annotation(
                        defiterm_type(
                            begin=term_defined.begin,
                            end=term_defined.end,
                            term=term_defined.term,
                            confidence=term_defined.tfidfValue,
                        )
                    )
                    logger.debug("Found definition term: %s", term_defined.get_covered_text())

        # store terms + definitions in a list of definitions
        definitions.append(term_definitions)

        # Keep track of definitions alone
        if len(term_definitions) and sentence.begin not in term_definition_uniq_idx:
            term_definition_uniq.append(sentence)
            term_definition_uniq_idx.append(sentence.begin)

        logger.debug("-----------------------------------------------------")

    # For solr
    for definition in term_definition_uniq:
        token_defined = definition.get_covered_text()
        start_defined = definition.begin
        end_defined = definition.end

        # Step 7: Send concept terms to Solr ('concept_defined' field)
        if len(token_defined.encode("utf-8")) < 32000:
            token_to_add_defined = {"t": token_defined, "s": start_defined, "e": end_defined, "y": "word"}
            concept_defined_tokens.insert(j, token_to_add_defined)
            j = j + 1

    # For django
    for group in definitions:
        concept_group = []
        for term, definition in group:
            lemma_name = ""
            token_defined = definition.get_covered_text()
            start_defined = definition.begin
            end_defined = definition.end

            if len(token_defined.encode("utf-8")) < 32000:
                if len(term.get_covered_text()) <= 200:
                    # Save Term Definitions in Django
                    c = Concept.objects.update_or_create(
                        name=term.get_covered_text(),
                        definition=token_defined,
                        lemma=lemma_name,
                        version=EXTRACT_TERMS_NLP_VERSION,
                        defaults={"website_id": django_doc.website.id},
                    )
                    concept_group.append(c[0])
                    defs = ConceptDefined.objects.filter(concept=c[0], document=django_doc)
                    if len(defs) == 1:
                        cd = defs[0]
                        cd.begin = start_defined
                        cd.end = end_defined
                        cd.save()
                    else:
                        ConceptDefined.objects.create(
                            concept=c[0], document=django_doc, startOffset=start_defined, endOffset=end_defined
                        )
                else:
                    logger.info(
                        "WARNING: Term '%s' has been skipped because the term name was too long. "
                        "Consider disabling supergrams or change the length in the database",
                        token,
                    )
        # Link definitions
        if len(concept_group) > 1:
            i = 0
            for from_concept in concept_group[i:]:
                for to_concept in concept_group[i + 1 :]:
                    from_concept.other.add(to_concept)
                i = i + 1

    # Step 5: Send term extractions to Solr (term_occurs field)

    # Convert the output to a readable format for Solr
    atomic_update = [
        {
            "id": document["id"],
            "concept_occurs": {"set": {"v": "1", "str": cas2.get_view(sofa_id_html2text).sofa_string, "tokens": []}},
        }
    ]
    concept_occurs_tokens = atomic_update[0]["concept_occurs"]["set"]["tokens"]

    # Select all Tfidfs from the CAS
    i = 0
    for term in cas2.get_view(sofa_id_html2text).select(TFIDF_CLASS):
        # FIXME: check if convered text ends with a space ?
        # Save the token information
        token = term.get_covered_text()
        score = term.tfidfValue
        start = term.begin
        end = term.end

        # Encode score base64
        encoded_bytes = base64.b64encode(score.encode("utf-8"))
        encoded_score = str(encoded_bytes, "utf-8")

        token_to_add = {"t": token, "s": start, "e": end, "y": "word", "p": encoded_score}
        concept_occurs_tokens.insert(i, token_to_add)
        i = i + 1

        # Retrieve the lemma for the term
        lemma_name = ""
        for lemma in cas2.get_view(sofa_id_html2text).select_covered(LEMMA_CLASS, term):
            if term.begin == lemma.begin and term.end == lemma.end:
                lemma_name = lemma.value

        # Store fisma term
        cas2.get_view(sofa_id_html2text).add_annotation(
            term_type(begin=term.begin, end=term.end, term=lemma_name, confidence=term.tfidfValue)
        )

        queryset = Concept.objects.filter(name=term.get_covered_text())
        if not queryset.exists():
            # Save Term Definitions in Django
            if len(term.get_covered_text()) <= 200:
                c = Concept.objects.update_or_create(
                    name=term.get_covered_text(),
                    lemma=lemma_name,
                    version=EXTRACT_TERMS_NLP_VERSION,
                    defaults={"website_id": django_doc.website.id},
                )
                ConceptOccurs.objects.update_or_create(
                    concept=c[0],
                    document=django_doc,
                    probability=float(score.encode("utf-8")),
                    startOffset=start,
                    endOffset=end,
                )

            else:
                logger.info(
                    "WARNING: Term '%s' has been skipped because the term name was too long. "
                    "Consider disabling supergrams or change the length in the database",
                    token,
                )

    logger.info("Complete CAS handling took %s seconds to succeed .", time.time() - start_cas)

    # Step 6: Post term_occurs to Solr
    escaped_json = json.dumps(atomic_update[0]["concept_occurs"]["set"])
    atomic_update[0]["concept_occurs"]["set"] = escaped_json
    logger.info("Detected %s concepts in document: %s", len(concept_occurs_tokens), document["id"])
    if len(concept_occurs_tokens) > 0:
        post_pre_analyzed_to_solr(atomic_update)

    # Step 8: Post term_defined to Solr
    escaped_json_def = json.dumps(atomic_update_defined[0]["concept_defined"]["set"])
    atomic_update_defined[0]["concept_defined"]["set"] = escaped_json_def
    logger.info("Detected %s concept definitions in document: %s", len(concept_defined_tokens), document["id"])
    if len(concept_defined_tokens) > 0:
        post_pre_analyzed_to_solr(atomic_update_defined)

    # Clean up annotations for Webanno
    annotations_to_remove = [
        VALUE_BETWEEN_TAG_TYPE_CLASS,
        DEPENDENCY_CLASS,
        LEMMA_CLASS,
        TFIDF_CLASS,
        SENTENCE_CLASS,
        PARAGRAPH_CLASS,
        TOKEN_CLASS,
    ]
    for remove in annotations_to_remove:
        for anno in cas2.get_view(sofa_id_html2text).select(remove):
            cas2.get_view(sofa_id_html2text).remove_annotation(anno)

    # Save CAS to MINIO
    minio_client = Minio(
        os.environ["MINIO_STORAGE_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )
    bucket_name = "cas-files"
    try:
        minio_client.make_bucket(bucket_name)
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass

    logger.info("Created bucket: %s", bucket_name)
    filename = document["id"] + "-" + EXTRACT_TERMS_NLP_VERSION + ".xml.gz"

    file = save_compressed_cas(cas2, filename)
    logger.info("Saved gzipped cas: %s", file.name)

    minio_client.fput_object(bucket_name, file.name, filename)
    logger.info("Uploaded to minio")

    os.remove(file.name)
    logger.info("Removed file from system")


def generate_typesystem_fisma():
    typesystem = TypeSystem()

    # Term
    term_type = typesystem.create_type(name="com.crosslang.fisma.Term")
    typesystem.add_feature(type_=term_type, name="term", rangeTypeName="uima.cas.String")
    typesystem.add_feature(type_=term_type, name="confidence", rangeTypeName="uima.cas.Float")

    # Definition
    typesystem.create_type(name="com.crosslang.fisma.Definition")

    # DefinitionTerm
    typesystem.create_type(name="com.crosslang.fisma.DefinitionTerm", supertypeName=term_type.name)

    return typesystem


@shared_task
def send_document_to_webanno(document_id):
    client = Pycaprio("http://webanno:8080", authentication=("admin", "admin"))
    # List projects
    projects = client.api.projects()
    project = projects[0]
    logger.info("PROJECT: %s", project)
    # Load CAS from Minio
    minio_client = Minio(
        os.environ["MINIO_STORAGE_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )
    try:
        cas_gz = minio_client.get_object("cas-files", document_id + "-" + EXTRACT_TERMS_NLP_VERSION + ".xml.gz")
    except NoSuchKey:
        return None

    # Load typesystems
    merged_ts = merge_typesystems(fetch_typesystem(), generate_typesystem_fisma())

    cas = load_compressed_cas(cas_gz, merged_ts)

    # # Clean up annotations for Webanno
    SOFA_ID_HTML2TEXT = "html2textView"
    # Modify cas to make html2textview the _InitialView
    cas._sofas["_InitialView"] = cas._sofas[SOFA_ID_HTML2TEXT]
    del cas._sofas[SOFA_ID_HTML2TEXT]
    cas._views["_InitialView"] = cas._views[SOFA_ID_HTML2TEXT]
    del cas._views[SOFA_ID_HTML2TEXT]
    cas._sofas["_InitialView"].sofaID = "_InitialView"
    cas._sofas["_InitialView"].sofaNum = 1
    cas._sofas["_InitialView"].xmiID = 1

    cas_xmi = cas.to_xmi()

    new_document = client.api.create_document(
        project,
        document_id,
        cas_xmi.encode(),
        document_format=InceptionFormat.XMI,
        document_state=DocumentState.ANNOTATION_IN_PROGRESS,
    )
    logger.info("NEWDOC: %s", new_document)
    return new_document


@shared_task
def export_all_user_data(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    documents = Document.objects.filter(website=website)
    logger.info("Exporting User Annotations to Minio CAS files for website: %s", website_name)

    # Load CAS from Minio
    minio_client = Minio(
        os.environ["MINIO_STORAGE_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False,
    )

    # Load typesystem
    with open(TYPESYSTEM_USER, "rb") as f:
        # Generate and write tempfile for typesystem.xml
        typesystem_user = load_typesystem(f)

    ts_fisma = generate_typesystem_fisma()
    typesystem = merge_typesystems(typesystem_user, ts_fisma)

    for document in documents:
        logger.info("Extracting document: %s", str(document.id))

        try:
            cas_gz = minio_client.get_object(
                "cas-files", str(document.id) + "-" + EXTRACT_TERMS_NLP_VERSION + ".xml.gz"
            )

            cas = load_compressed_cas(cas_gz, typesystem)

            annotations = AnnotationWorklog.objects.filter(document=document)
            for annotation in annotations:
                user = ""
                role = ""
                if annotation.user:
                    user = annotation.user.username
                    role = annotation.user.groups.name

                date = annotation.created_at
                if annotation.concept_occurs is not None:
                    occurs_type = typesystem_user.get_type(TFIDF_CLASS)
                    begin = annotation.concept_occurs.startOffset
                    end = annotation.concept_occurs.endOffset

                    cas.get_view(sofa_id_html2text).add_annotation(
                        occurs_type(begin=begin, end=end, user=user, role=role, datetime=date)
                    )
                else:
                    defined_type = typesystem.get_type(DEFINED_TYPE)
                    begin = annotation.concept_defined.startOffset
                    end = annotation.concept_defined.endOffset

                    cas.get_view(sofa_id_html2text).add_annotation(
                        defined_type(begin=begin, end=end, user=user, role=role, datetime=date)
                    )

            filename = str(document.id) + "-" + EXTRACT_TERMS_NLP_VERSION + ".xml.gz"
            file = save_compressed_cas(cas, filename)
            logger.info("Saved gzipped cas: %s", file.name)

            minio_client.fput_object("cas-files", file.name, filename)
            logger.info("Uploaded to minio")

            os.remove(file.name)
            logger.info("Removed file from system")

        except NoSuchKey:
            pass


@shared_task
def export_public_services(website_id):
    website = Website.objects.get(pk=website_id)
    public_services = get_public_services(RDF_FUSEKI_URL, website.url)

    for ps in public_services:
        uri = str(ps["uri"])
        title = str(ps["title"])
        description = str(ps["description"])

        # Add website here
        obj = PublicService.objects.update_or_create(
            name=title, description=description, defaults={"identifier": uri, "website_id": website.id}
        )
        logger.info("PublicService: %s", obj[0].name)


@shared_task
def export_contact_points(website_id):
    website = Website.objects.get(pk=website_id)
    contact_points = get_contact_points(RDF_FUSEKI_URL, website.url)

    for cp in contact_points:
        uri = str(cp["uri"])

        cp_details = get_contact_point_info(RDF_FUSEKI_URL, uri)

        pred_list = []
        label_list = []
        for cp_detail in cp_details:
            pred_list.append(str(cp_detail["pred"]))
            label_list.append(str(cp_detail["label"]))

        description = "\n".join(label_list)

        obj = ContactPoint.objects.update_or_create(
            identifier=uri,
            defaults={"description": description, "identifier": uri, "pred": pred_list, "website_id": website.id},
        )
        logger.info("ContactPoint: %s", obj[0].description)


@shared_task
def export_websites_from_rdf():
    websites = get_graphs(RDF_FUSEKI_URL)

    for g in websites:
        graph = str(g["graph"])

        obj = Website.objects.update_or_create(url=graph)
        if len(obj[0].name) == 0:
            obj[0].name = graph
            obj[0].save()
