import os

import pysolr

ROW_LIMIT = 250000


def solr_search(core="", term=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results_highlighted(client.search(term,
                                                   **{'rows': ROW_LIMIT, 'hl': 'on', 'hl.fl': '*',
                                                      'hl.snippets': 100, 'hl.maxAnalyzedChars': 1000000,
                                                      'hl.simple.pre': '<span class="highlight">',
                                                      'hl.simple.post': '</span>'}))
    return search


def solr_search_paginated(core="", term="", page_number=1, rows_per_page=10):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    # solr page starts at 0
    page_number = int(page_number) - 1
    start = page_number * int(rows_per_page)
    result = client.search(term,
                           **{'rows': rows_per_page,
                              'start': start,
                              'hl': 'on', 'hl.fl': '*',
                              'hl.snippets': 100, 'hl.maxAnalyzedChars': 1000000,
                              'hl.simple.pre': '<span class="highlight">',
                              'hl.simple.post': '</span>'})
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


def solr_search_website_sorted(core="", website=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search(
        'website:' + website, **{'rows': ROW_LIMIT, 'sort': 'id asc'}))
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


def solr_add(core="", docs=[]):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    client.add(docs, commit=True)


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
