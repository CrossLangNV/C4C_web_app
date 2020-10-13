import os

import pysolr
import textdistance

ROW_LIMIT = 250000


def solr_search(core="", term=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results_highlighted(client.search(term,
                                                   **{'rows': ROW_LIMIT, 'hl': 'on', 'hl.fl': '*',
                                                      'hl.snippets': 100, 'hl.maxAnalyzedChars': 1000000,
                                                      'hl.simple.pre': '<span class="highlight">',
                                                      'hl.simple.post': '</span>'}))
    return search


def solr_search_website_paginated(core="", q="", page_number=1, rows_per_page=10):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    # solr page starts at 0
    page_number = int(page_number) - 1
    start = page_number * int(rows_per_page)
    options = {'rows': rows_per_page, 'start': start}
    return client.search(q, **options)


def solr_search_paginated(core="", term="", page_number=1, rows_per_page=10, ids_to_filter_on=None,
                          sort_by=None, sort_direction='asc'):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    # solr page starts at 0
    page_number = int(page_number) - 1
    start = page_number * int(rows_per_page)
    if core == 'documents':
        term = 'content:"' + term + '"'
    options = {'rows': rows_per_page,
               'start': start,
               'hl': 'on', 'hl.fl': '*',
               'hl.requireFieldMatch': 'true',
               'hl.snippets': 3, 'hl.maxAnalyzedChars': -1,
               'hl.simple.pre': '<span class="highlight">',
               'hl.simple.post': '</span>'}
    if ids_to_filter_on:
        fq_ids = 'id:(' + ' OR '.join(ids_to_filter_on) + ')'
        options['fq'] = fq_ids
    if sort_by:
        options['sort'] = sort_by + ' ' + sort_direction
    result = client.search(term, **options)
    search = get_results_highlighted(result)
    num_found = result.raw_response['response']['numFound']
    return num_found, search


def solr_search_query_paginated(core="", term="", page_number=1, rows_per_page=10, ids_to_filter_on=None,
                                sort_by=None, sort_direction='asc'):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    # solr page starts at 0
    page_number = int(page_number) - 1
    start = page_number * int(rows_per_page)
    options = {'rows': rows_per_page,
               'start': start,
               'hl': 'on', 'hl.fl': '*',
               'hl.requireFieldMatch': 'true',
               'hl.snippets': 3, 'hl.maxAnalyzedChars': -1,
               'hl.simple.pre': '<span class="highlight">',
               'hl.simple.post': '</span>'}
    if ids_to_filter_on:
        fq_ids = 'id:(' + ' OR '.join(ids_to_filter_on) + ')'
        options['fq'] = fq_ids
    if sort_by:
        options['sort'] = sort_by + ' ' + sort_direction
    result = client.search(term, **options)
    search = get_results_highlighted(result)
    num_found = result.raw_response['response']['numFound']
    return num_found, search


def solr_search_query_paginated_preanalyzed(core="", term="", page_number=1, rows_per_page=10,
                                            sort_by=None, sort_direction='asc'):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    # solr page starts at 0
    page_number = int(page_number) - 1
    start = page_number * int(rows_per_page)
    options = {'rows': rows_per_page,
               'start': start,
               'fl': 'concept_defined,concept_occurs',
               'hl': 'on', 'hl.fl': 'concept_defined,concept_occurs',
               'hl.simple.pre': '<span class="highlight">',
               'hl.simple.post': '</span>'}
    if sort_by:
        options['sort'] = sort_by + ' ' + sort_direction
    result = client.search(term, **options)
    search = get_results_highlighted(result)
    num_found = result.raw_response['response']['numFound']
    return num_found, search


def solr_search_id(core="", id=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search('id:' + id, **{'rows': ROW_LIMIT}))
    return search


def solr_search_id_sorted(core="", id=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search(
        'id:' + id, **{'rows': ROW_LIMIT, 'sort': 'id asc'}))
    return search


def solr_search_website_with_content(core="", website="", **kwargs):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    date = kwargs.get('date', None)
    query = 'website:' + website

    if date:
        query = query + " AND date:["+date+" TO NOW]"
    search = client.search(
        query, **{'rows': 250, 'start': 0, 'cursorMark': "*", 'sort': 'id asc'})
    return search


def solr_search_website_sorted(core="", website="", **kwargs):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    SOLR_SYNC_FIELDS = 'id,title,title_prefix,author,status,type,date,date_last_update,url,eli,celex,file_url,website,summary,various,consolidated_versions'
    date = kwargs.get('date', None)
    query = 'website:' + website

    if date:
        query = query + " AND date:["+date+" TO NOW]"
    search = get_results(client.search(
        query, **{'rows': ROW_LIMIT, 'fl': SOLR_SYNC_FIELDS, 'sort': 'id asc'}))
    return search


def solr_search_document_id_sorted(core="", document_id=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search(
        'attr_document_id:"' + document_id + '"', **{'rows': ROW_LIMIT, 'sort': 'id asc'}))
    return search


def get_results(response):
    results = []
    for doc in response:
        results.append(doc)
    return results


def get_results_highlighted(response):
    results = []
    # iterate over docs
    for doc in response:
        # iterate over every key in single doc dictionary
        for key in doc:
            if key in response.highlighting[doc['id']]:
                doc[key] = response.highlighting[doc['id']][key]
        results.append(doc)
    return results


def solr_update(core, document):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    document_existing_result = client.search('id:' + str(document['id']))
    if len(document_existing_result.docs) == 1:
        document_existing = document_existing_result.docs[0]
        for key, value in document.items():
            if key == 'file':
                document_existing[key] = value.name
            elif key != 'id':
                document_existing[key] = value
        client.add([document_existing], commit=True)
    else:
        client.add([document], commit=True)


def solr_add_file(core, file, file_id, file_url, document_id):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    extra_params = {
        'commit': 'true',
        'literal.id': file_id,
        'resource.name': file.name,
        'literal.url': file_url,
        'literal.document_id': document_id
    }
    client.extract(file, extractOnly=False, **extra_params)


def solr_delete(core, id):
    try:
        client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
        client.delete(id=id)
        client.commit()
    except pysolr.SolrError:
        pass


'''
Use Solr MoreLikeThis https://lucene.apache.org/solr/guide/8_5/morelikethis.html 
to find similar documents given a document id. Solr MLT returns candidates, apply coefficient to candidates 
upon which a threshold can be applied: see https://www.dexstr.io/finding-duplicates-large-set-files/.
'''


def solr_mlt(core, id, mlt_field='title,content', number_candidates=5, threshold=0.0):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search_result = client.search('id:' + id, **{'mlt': 'true',
                                                 'mlt.fl': mlt_field,
                                                 'mlt.count': number_candidates,
                                                 'fl': 'id,website,' + mlt_field})
    # document to compare against
    base_doc = search_result.docs[0]
    base_tokens = base_doc['content'][0].split()

    # list of similar documents with Jaccard coefficient
    similar_documents_with_coeff = []
    for doc in search_result.raw_response['moreLikeThis'][id]['docs']:
        candidate_tokens = doc['content'][0].split()
        similarity = textdistance.jaccard(base_tokens, candidate_tokens)
        if similarity > float(threshold):
            similar_documents_with_coeff.append((doc['id'], doc['title'][0], doc['website'][0], similarity))

    # sort descending on coefficient
    similar_documents_with_coeff.sort(key=lambda x: x[-1], reverse=True)

    return similar_documents_with_coeff
