import pysolr
import os


def solr_search(core="", term=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results_highlighted(client.search(term,
                                       **{'rows': 10000, 'hl': 'on', 'hl.fl': '*',
                                          'hl.simple.pre': '<span class="highlight">',
                                          'hl.simple.post': '</span>'}))
    return search

def solr_search_id(core="", id=""):
    client = pysolr.Solr(os.environ['SOLR_URL'] + '/' + core)
    search = get_results(client.search('id:' + id))
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

if __name__ == '__main__':
    term = "film"
    print("Search films | term = " + term + ":\n", solr_search(core="films", term=term))
