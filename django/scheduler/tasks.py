from __future__ import absolute_import, unicode_literals

import base64
import csv
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
from celery import shared_task, chain
from django.core.exceptions import ValidationError
from jsonlines import jsonlines
from minio import Minio, ResponseError
from minio.error import BucketAlreadyOwnedByYou, BucketAlreadyExists
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from tika import parser
from twisted.internet import reactor

from glossary.models import Concept
from searchapp.datahandling import score_documents
from searchapp.models import Website, Document, AcceptanceState, Tag, AcceptanceStateValue
from searchapp.solr_call import solr_search_website_sorted, solr_search_website_with_content

logger = logging.getLogger(__name__)
workpath = os.path.dirname(os.path.abspath(__file__))

sofa_id = "html2textView"
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
def full_service_task(website_id):
    website = Website.objects.get(pk=website_id)
    logger.info("Full service for WEBSITE: %s", website.name)
    # the following subtasks are linked together in order:
    # sync_scrapy_to_solr -> parse_content -> sync (solr to django) -> score
    # a task only starts after the previous finished, immutable signatures (si)
    # are used since a task doesn't need the result of the previous task: see
    # https://docs.celeryproject.org/en/stable/userguide/canvas.html
    chain(
        sync_scrapy_to_solr_task.si(website_id),
        parse_content_to_plaintext_task.si(website_id),
        sync_documents_task.si(website_id),
        score_documents_task.si(website_id)
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
def test_solr_preanalyzed_update():
    logger.info("To be removed.")


@shared_task
def extract_terms(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    core = 'documents'
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"

    # Query for Solr to find per website that has the content_html field (some do not)
    q = "website:" + website_name + " AND content_html:* AND acceptance_state:accepted"

    # Load all documents from Solr
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    options = {'rows': rows_per_page, 'start': page_number,
               'cursorMark': cursor_mark, 'sort': 'id asc', 'fl': 'content_html,id'}
    documents = client.search(q, **options)

    for document in documents:
        if document['content_html'] is not None:
            if len(document['content_html'][0]) > 100000:
                logger.info("Skipping too big document id: %s", document['id'])
                continue

            logger.info("Extracting terms from document id: %s",
                        document['id'])

            content_html_text = {
                "text": document['content_html'][0]
            }

            # Step 1: Html2Text - Get XMI from UIMA
            start = time.time()
            r = requests.post(
                UIMA_URL["BASE"] + UIMA_URL["HTML2TEXT"], json=content_html_text)
            if r.status_code == 200:
                logger.info('Sent request to %s. Status code: %s', UIMA_URL["BASE"] + UIMA_URL["HTML2TEXT"],
                            r.status_code)
                end = time.time()
                logger.info(
                    "UIMA Html2Text took %s seconds to succeed.", end-start)

                # Step 2: NLP Term Definitions
                # Write tempfile for typesystem.xml
                typesystem_req = requests.get(
                    UIMA_URL["BASE"] + UIMA_URL["TYPESYSTEM"])
                typesystem_file = open("typesystem_tmp.xml", "w")
                typesystem_file.write(typesystem_req.content.decode("utf-8"))

                # Write tempfile for cas.xml
                with open(typesystem_file.name, 'rb') as f:
                    ts = cassis.load_typesystem(f)

                content_decoded = r.content.decode('utf-8')
                encoded_bytes = base64.b64encode(
                    content_decoded.encode("utf-8"))
                encoded_b64 = str(encoded_bytes, "utf-8")

                input_for_term_defined = {
                    "cas_content": encoded_b64,
                    "content_type": "html"
                }

                start = time.time()
                definitions_request = requests.post(DEFINITIONS_EXTRACT_URL,
                                                    json=input_for_term_defined)
                end = time.time()
                logger.info("Sent request to DefinitionExtract NLP. Status code: %s",
                            definitions_request.status_code)
                logger.info(
                    "DefinitionExtract took %s seconds to succeed.", end-start)
                definitions_decoded_cas = base64.b64decode(
                    json.loads(definitions_request.content)['cas_content']).decode("utf-8")

                # Step 3: NLP TextExtract
                text_cas = {
                    "cas_content": json.loads(definitions_request.content)['cas_content'],
                    "content_type": "html"
                }
                start = time.time()
                request_nlp = requests.post(TERM_EXTRACT_URL, json=text_cas)
                end = time.time()
                logger.info(
                    "Sent request to TextExtract NLP. Status code: %s", request_nlp.status_code)
                logger.info(
                    "TermExtract took %s seconds to succeed.", end-start)
                decoded_cas_plus = base64.b64decode(json.loads(request_nlp.content)[
                                                    'cas_content']).decode("utf-8")

                # Step 4: Text2Html - Send CAS+ (XMI) to UIMA - TERM EXTRACT
                cas_plus_content = json.loads(request_nlp.content)
                decoded_cas_plus = base64.b64decode(
                    cas_plus_content['cas_content']).decode("utf-8")
                cas_plus_text_json = {
                    "text": decoded_cas_plus[39:]
                }

                start = time.time()
                request_text_to_html = requests.post(UIMA_URL["BASE"] + UIMA_URL["TEXT2HTML"],
                                                     json=cas_plus_text_json)
                end = time.time()
                logger.info("Sent request to %s. Status code: %s", UIMA_URL["BASE"] + UIMA_URL["TEXT2HTML"],
                            request_text_to_html.status_code)
                logger.info(
                    "UIMA Text2Html took %s seconds to succeed.", end - start)
                terms_decoded_cas = request_text_to_html.content.decode(
                    "utf-8")

                # Step 4: Text2Html - Send CAS+ (XMI) to UIMA - DEFINITION EXTRACT
                cas_plus_content = json.loads(definitions_request.content)
                decoded_cas_plus = base64.b64decode(
                    cas_plus_content['cas_content']).decode("utf-8")
                cas_plus_text_json = {
                    "text": decoded_cas_plus[39:]
                }
                # logger.info("definitions json sent to %s: %s", UIMA_URL["BASE"] + UIMA_URL["TEXT2HTML"],
                #             cas_plus_text_json)
                request_text_to_html = requests.post(UIMA_URL["BASE"] + UIMA_URL["TEXT2HTML"],
                                                     json=cas_plus_text_json)
                logger.info("Sent request to /text2html. Status code: %s",
                            request_text_to_html.status_code)
                definitions_decoded_cas = request_text_to_html.content.decode(
                    "utf-8")

                # Load CAS from NLP
                cas = cassis.load_cas_from_xmi(
                    definitions_decoded_cas, typesystem=ts)
                cas2 = cassis.load_cas_from_xmi(
                    terms_decoded_cas, typesystem=ts)

                atomic_update_defined = [
                    {
                        "id": document['id'],
                        "concept_defined": {"set": {
                            "v": "1",
                            "str": cas.sofa_string,
                            "tokens": [

                            ]
                        }}
                    }
                ]
                concept_defined_tokens = atomic_update_defined[0]['concept_defined']['set']['tokens']
                j = 0

                # Term defined, we check which terms are covered by definitions
                for defi in cas.get_view(sofa_id_text2html).select(
                        "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"):
                    for term in cas2.get_view(sofa_id_text2html).select_covered(
                            "de.tudarmstadt.ukp.dkpro.core.api.frequency.tfidf.type.Tfidf",
                            defi):
                        # Save Term Definitions in Django
                        Concept.objects.update_or_create(name=term.get_covered_text(), defaults={
                                                         'definition': defi.get_covered_text()[:-4]})

                        # Step 7: Send concept terms to Solr ('concept_defined' field)
                        token_defined = defi.get_covered_text()
                        start_defined = defi.begin

                        # TODO change end to end-4 because of bug
                        end_defined = defi.end
                        if token_defined.endswith(" </p>"):
                            end_defined = defi.end-4
                            token_defined = token_defined[:-4]

                        token_to_add_defined = {
                            "t": token_defined,
                            "s": start_defined,
                            "e": end_defined,
                            "y": "word"
                        }
                        concept_defined_tokens.insert(j, token_to_add_defined)
                        j = j + 1

                        logger.info(
                            "[concept_defined] Added term '%s' to the PreAnalyzed payload (j=%d) (token pos: %s-%s)",
                            token_defined, j, start_defined, end_defined)

                # Step 5: Send term extractions to Solr (term_occurs field)

                # Convert the output to a readable format for Solr
                atomic_update = [
                    {
                        "id": document['id'],
                        "concept_occurs": {
                            "set": {
                                "v": "1",
                                "str": cas2.sofa_string,
                                "tokens": [

                                ]
                            }
                        }
                    }
                ]
                concept_occurs_tokens = atomic_update[0]['concept_occurs']['set']['tokens']

                # Select all Tfidfs from the CAS
                i = 0
                for term in cas2.get_view(sofa_id_text2html).select("de.tudarmstadt.ukp.dkpro.core.api.frequency.tfidf.type.Tfidf"):
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

                    # Save Term Definitions in Django
                    Concept.objects.update_or_create(
                        name=term.get_covered_text())

                    logger.info("[concept_occurs] Added term '%s' to the PreAnalyzed payload (i=%d) (token pos: %s-%s)",
                                token, i, start, end)

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
def score_documents_task(website_id):
    # lookup documents for website and score them
    website = Website.objects.get(pk=website_id)
    logger.info("Scoring documents with WEBSITE: " + website.name)
    solr_documents = solr_search_website_with_content(
        'documents', website.name)
    score_documents(website.name, solr_documents)


@shared_task
def sync_documents_task(website_id):
    # lookup documents for website and sync them
    website = Website.objects.get(pk=website_id)
    logger.info("Syncing documents with WEBSITE: " + website.name)
    # query Solr for available documents and sync with Django
    solr_documents = solr_search_website_sorted(
        core='documents', website=website.name.lower())
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
            "language": solr_doc.get('language', ''),
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


@shared_task
def launch_fullsite_crawler(url, website, language):
    scrapy_settings_path = 'scraper.scrapy_app.settings'
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', scrapy_settings_path)
    settings = get_project_settings()
    settings['celery_id'] = launch_crawler.request.id
    runner = CrawlerRunner(settings=settings)
    d = runner.crawl('fullsite', url=url, website=website, language=language)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()  # the script will block here until the crawling is finished


@shared_task
def launch_fullsite_multiple(urls, websites):
    for url, website in zip(urls, websites):
        launch_fullsite_crawler.delay(url, website)


@shared_task
def launch_fullsite_flanders(number_websites):
    with open(workpath + '/websites/flanders_municipalities.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count < number_websites:
                launch_fullsite_crawler.delay(row[0], row[1], language='nl')
                line_count += 1


@shared_task()
def parse_content_to_plaintext_task(website_id):
    website = Website.objects.get(pk=website_id)
    website_name = website.name.lower()
    logger.info('Adding content to each %s document.', website_name)
    page_number = 0
    rows_per_page = 250
    cursor_mark = "*"
    # Make sure solr index is updated
    core = 'documents'
    requests.get(os.environ['SOLR_URL'] +
                 '/' + core + '/update?commit=true')
    # select all records where content is empty and content_html is not
    q = "-content: [\"\" TO *] AND ( content_html: [* TO *] OR file_name: [* TO *] ) AND website:" + website_name
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
