import os

import pysolr


def solr_search(core="", term=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results_highlighted(client.search(term,
                                                   **{'rows': 10000, 'hl': 'on', 'hl.fl': '*',
                                                      'hl.snippets': 100, 'hl.maxAnalyzedChars': 1000000,
                                                      'hl.simple.pre': '<span class="highlight">',
                                                      'hl.simple.post': '</span>'}))
    return search


def solr_search_id(core="", id=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search('id:' + id, **{'rows': 10000}))
    return search


def solr_search_id_sorted(core="", id=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search('id:' + id, **{'rows': 10000, 'sort': 'id asc'}))
    return search


def solr_search_website_sorted(core="", website=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search('website:' + website, **{'rows': 10000, 'sort': 'id asc'}))
    return search


def solr_search_document_id_sorted(core="", document_id=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search('attr_document_id:' + document_id, **{'rows': 10000, 'sort': 'id asc'}))
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
    print(docs)
    client.add(docs, commit=True)


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
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    client.delete(id=id)
    client.commit()


def solr_delete_all(core):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    client.delete(q='*:*')
    client.commit()


if __name__ == '__main__':
    os.environ['SOLR_URL'] = 'http://localhost:8983/solr'

    # Search
    # term = "film"
    # print("Search films | term = " + term + ":\n", solr_search(core="films", term=term))

    # File save
    # base_dir = os.path.dirname(os.getcwd())
    # media_dir = os.path.join(base_dir, 'media')
    # test_file_path = os.path.join(media_dir, os.listdir(media_dir)[0])
    # test_file = open(test_file_path, 'rb')
    # solr_add_file('files', test_file, '0')

    # Delete
    solr_delete_all('files')
